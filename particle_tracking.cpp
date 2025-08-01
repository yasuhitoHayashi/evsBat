#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <deque>
#include <vector>
#include <tuple>
#include <cmath>
#include <algorithm>
#include <limits>

// Struct to store the result of particle tracking
struct ParticleResult {
    int particle_id; // Particle ID
    std::vector<std::tuple<float, double, double>> centroid_history;  // History of centroids(time, centroid_x, centroid_y)
    std::vector<std::tuple<int, int, float>> events;  // List of events(x, y, time)
};

// Class to track and manage particles
class Particle {
public:
    int particle_id; // Particle ID
    std::deque<std::tuple<int, int, float>> events;  // List of events: (x, y, time)
    std::deque<std::tuple<int, int, float>> recent_events;  // Recent events for centroid calculation
    double centroid_x, centroid_y; // Current centroid coordinates of the particle
    int mass; // Number of events belonging to the particle
    std::deque<std::tuple<float, double, double>> centroid_history;  // History of centroids(time, centroid_x, centroid_y)

    // Constructor. Initializes a Particle. Called when creating a new particle and adds the initial event.
    Particle(int id, int x, int y, float time) : particle_id(id), centroid_x(x), centroid_y(y), mass(1) {
        events.push_back(std::make_tuple(x, y, time)); // Add the initial event
        recent_events.push_back(std::make_tuple(x, y, time));  // Add to recent events
        centroid_history.push_back(std::make_tuple(time, centroid_x, centroid_y)); // Add to centroid history
    }

    // Function to merge another particle into this particle. Adds the events of the other particle and integrates mass.
    void merge(const Particle& other) {
        // Add all events from the other particle
        for (const auto& event : other.events) {
            events.push_back(event);
            recent_events.push_back(event);  // Also add to recent_events
        }

        // Merge mass
        mass += other.mass;

        // Recalculate centroid (weighted average based on mass)
        double total_mass = mass + other.mass;
        centroid_x = (centroid_x * mass + other.centroid_x * other.mass) / total_mass;
        centroid_y = (centroid_y * mass + other.centroid_y * other.mass) / total_mass;

        // Update centroid history
        if (!recent_events.empty()) {
            float time = std::get<2>(recent_events.back());
            centroid_history.push_back(std::make_tuple(time, centroid_x, centroid_y));
        }
    }

    // Function to add a new event to a particle. Also updates centroid and history.
    void add_event(int x, int y, float time) {
        events.push_back(std::make_tuple(x, y, time));
        recent_events.push_back(std::make_tuple(x, y, time));  // Also add to recent_events
        mass++; // Increase mass

        // Remove old events (remove events older than 2000us)
        float cutoff_time = time - 2000.0;
        while (!recent_events.empty() && std::get<2>(recent_events.front()) < cutoff_time) {
            recent_events.pop_front();
        }

        // Recalculate centroid by averaging x and y of all events
        if (!recent_events.empty()) {
            double sum_x = 0, sum_y = 0;
            for (const auto& event : recent_events) {
                sum_x += std::get<0>(event);
                sum_y += std::get<1>(event);
            }
            centroid_x = sum_x / recent_events.size();
            centroid_y = sum_y / recent_events.size();
        }

        // Save the current centroid to history
        centroid_history.push_back(std::make_tuple(time, centroid_x, centroid_y));
    }

    // Function to check if a particle is active based on time and mass
    bool is_active(float current_time, int m_threshold) const {
        if (!events.empty() && std::get<2>(events.back()) < current_time - 2000.0) {
            return mass > m_threshold;  // If no event exists within the last 2000us, return whether mass exceeds threshold
        }
        return true;  // If there is an event within 2000us, always active
    }

    // Final active check function based only on mass (used to remove small particles at the last time step)
    bool is_active_final(int m_threshold) const {
        return mass > m_threshold;
    }

    // Function to convert Particle into a ParticleResult object to be returned to Python
    ParticleResult get_result() const {
        ParticleResult result;
        result.particle_id = particle_id;
        result.centroid_history = std::vector<std::tuple<float, double, double>>(centroid_history.begin(), centroid_history.end());
        result.events = std::vector<std::tuple<int, int, float>>(events.begin(), events.end());
        return result;
    }
};

// Gaussian distance calculation. Computes spatial (x, y) and temporal (t) distance between two events and returns a score based on a Gaussian distribution.
// sigma_x is the spatial standard deviation of the Gaussian distribution, and sigma_t is the temporal standard deviation.
double gaussian_distance(int x1, int y1, float t1, int x2, int y2, float t2, double sigma_x, double sigma_t) {
    double spatial_distance_sq = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2);  // // Spatial distance squared
    double time_distance_sq = (t1 - t2) * (t1 - t2);  // Temporal distance squared
    return std::exp(-spatial_distance_sq / (2 * sigma_x * sigma_x) - time_distance_sq / (2 * sigma_t * sigma_t));  // Score based on Gaussian distribution. Closer to 1 means events are closer in space-time.
}

// Event-based particle tracking algorithm. Takes in event data, tracks particles, and returns a final list of particles.
std::vector<ParticleResult> track_particles_cpp(const std::vector<std::tuple<int, int, float>>& data, double sigma_x, double sigma_t, double gaussian_threshold, int m_threshold) {
    // Create empty particle vector
    std::vector<Particle> particles;
    int particle_id_counter = 0; // Reset particle ID counter

    // Perform particle tracking for each event in the data
    for (const auto& event : data) {
        // Retrieve x, y, time from the event
        int x = std::get<0>(event);
        int y = std::get<1>(event);
        float time = std::get<2>(event);

        // Check whether the new event should be added to an existing particle
        bool found_overlap = false;
        size_t overlapping_particle_index = std::numeric_limits<size_t>::max(); //If overlap with existing particle found, store the index

        // For each particle (and its events), calculate distance from the new event to check for overlap
        for (size_t i = 0; i < particles.size(); ++i) {
            Particle& particle = particles[i];

            // Loop over recent events of the particle and calculate distance to new event
            for (const auto& recent_event : particle.recent_events) {
                // Calculate distance based on Gaussian distribution
                double gaussian_score = gaussian_distance(x, y, time, std::get<0>(recent_event), std::get<1>(recent_event), std::get<2>(recent_event), sigma_x, sigma_t);

                // If score exceeds threshold, add event index
                if (gaussian_score >= gaussian_threshold) {
                    particle.add_event(x, y, time);
                    found_overlap = true;
                    overlapping_particle_index = i;
                    break;
                }
            }
            if (found_overlap) {
                break;
            }
        }

        // If no overlap with any particle, create a new particle
        if (!found_overlap) {
            particle_id_counter++; // Add 1 to particle ID
            Particle new_particle(particle_id_counter, x, y, time);
            particles.push_back(new_particle);
        // If overlap exists, merge with overlapping particle
        } else if (overlapping_particle_index != std::numeric_limits<size_t>::max()) {
            // If the same event overlaps with multiple particles, compare recent events of the two particles and check for overlap. If threshold is exceeded, merge particles
            for (size_t i = 0; i < particles.size(); ++i) {
                if (i != overlapping_particle_index) {
                    Particle& particle = particles[i];

                    // Check overlap between two particles using same Gaussian distance condition
                    for (const auto& recent_event : particle.recent_events) {
                        double gaussian_score = gaussian_distance(
                            std::get<0>(particles[overlapping_particle_index].recent_events.back()),
                            std::get<1>(particles[overlapping_particle_index].recent_events.back()),
                            std::get<2>(particles[overlapping_particle_index].recent_events.back()),
                            std::get<0>(recent_event),
                            std::get<1>(recent_event),
                            std::get<2>(recent_event),
                            sigma_x, sigma_t);

                        if (gaussian_score >= gaussian_threshold) {
                            // Merge particles
                            particles[overlapping_particle_index].merge(particle);
                            particles.erase(particles.begin() + i);  // Remove after merge
                            break;
                        }
                    }
                }
            }
        }

        // Remove particles if more than 2000ms have passed since last event and mass is below threshold
        particles.erase(std::remove_if(particles.begin(), particles.end(),
            [time, m_threshold](const Particle& p) { return !p.is_active(time, m_threshold); }), particles.end());
    }

    // At final time step, remove particles whose mass is below threshold
    particles.erase(std::remove_if(particles.begin(), particles.end(),
        [m_threshold](const Particle& p) { return !p.is_active_final(m_threshold); }), particles.end());

    // Return results
    std::vector<ParticleResult> results;
    for (const auto& particle : particles) {
        results.push_back(particle.get_result());
    }

    return results;
}

PYBIND11_MODULE(particle_tracking, m) {
    pybind11::class_<ParticleResult>(m, "ParticleResult")
        .def_readonly("particle_id", &ParticleResult::particle_id)
        .def_readonly("centroid_history", &ParticleResult::centroid_history)
        .def_readonly("events", &ParticleResult::events);

    m.def("track_particles_cpp", &track_particles_cpp, "Track particles in C++");
}
