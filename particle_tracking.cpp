#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <deque>
#include <vector>
#include <tuple>
#include <cmath>
#include <algorithm>
#include <limits>
#include <aestream/aestream.hpp> // AEStreamのインクルード

// ...（ParticleResultとParticleクラスの定義、gaussian_distance関数）...

std::vector<ParticleResult> track_particles_from_stream(const std::string& file_path, double sigma_x, double sigma_t, double gaussian_threshold, int m_threshold) {
    // AEStreamのストリームを設定
    ae::input stream(file_path);
    
    std::vector<Particle> particles;
    int particle_id_counter = 0;

    // ストリームからイベントを逐次読み込み、追跡処理を行う
    for (const auto& event : stream) {
        int x = event.x;
        int y = event.y;
        float time = event.timestamp;

        bool found_overlap = false;
        size_t overlapping_particle_index = std::numeric_limits<size_t>::max();

        for (size_t i = 0; i < particles.size(); ++i) {
            Particle& particle = particles[i];
            for (const auto& recent_event : particle.recent_events) {
                double gaussian_score = gaussian_distance(x, y, time, std::get<0>(recent_event), std::get<1>(recent_event), std::get<2>(recent_event), sigma_x, sigma_t);

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

        if (!found_overlap) {
            particle_id_counter++;
            Particle new_particle(particle_id_counter, x, y, time);
            particles.push_back(new_particle);
        } else if (overlapping_particle_index != std::numeric_limits<size_t>::max()) {
            for (size_t i = 0; i < particles.size(); ++i) {
                if (i != overlapping_particle_index) {
                    Particle& particle = particles[i];
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
                            particles[overlapping_particle_index].merge(particle);
                            particles.erase(particles.begin() + i);
                            break;
                        }
                    }
                }
            }
        }

        particles.erase(std::remove_if(particles.begin(), particles.end(),
            [time, m_threshold](const Particle& p) { return !p.is_active(time, m_threshold); }), particles.end());
    }

    particles.erase(std::remove_if(particles.begin(), particles.end(),
        [m_threshold](const Particle& p) { return !p.is_active_final(m_threshold); }), particles.end());

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

    m.def("track_particles_from_stream", &track_particles_from_stream, "Track particles from AEStream input");
}
