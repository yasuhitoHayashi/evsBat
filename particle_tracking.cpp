#include <iostream>
#include <fstream>
#include <vector>
#include <deque>
#include <tuple>
#include <cmath>
#include <algorithm>
#include <limits>
#include <chrono>
#include <sstream>

namespace Metavision {
namespace Evt3 {
    // イベントタイプの列挙型
    enum class EventTypes : uint8_t {
        EVT_ADDR_Y = 0x0,
        EVT_ADDR_X = 0x2,
        VECT_BASE_X = 0x3,
        VECT_12 = 0x4,
        VECT_8 = 0x5,
        EVT_TIME_LOW = 0x6,
        EVT_TIME_HIGH = 0x8,
        EXT_TRIGGER = 0xA
    };

    // 各イベント用の構造体
    struct RawEvent { uint16_t pad : 12; uint16_t type : 4; };
    struct RawEventTime { uint16_t time : 12; uint16_t type : 4; };
    struct RawEventXAddr { uint16_t x : 11; uint16_t pol : 1; uint16_t type : 4; };
    struct RawEventVect12 { uint16_t valid : 12; uint16_t type : 4; };
    struct RawEventVect8 { uint16_t valid : 8; uint16_t unused : 4; uint16_t type : 4; };
    struct RawEventY { uint16_t y : 11; uint16_t orig : 1; uint16_t type : 4; };
    struct RawEventXBase { uint16_t x : 11; uint16_t pol : 1; uint16_t type : 4; };
    struct RawEventExtTrigger { uint16_t value : 1; uint16_t unused : 7; uint16_t id : 4; uint16_t type : 4; };

    using timestamp_t = uint64_t;

} // namespace Evt3
} // namespace Metavision

struct Metadata {
    int sensor_width = 1280, sensor_height = 720;
};

struct ParticleResult {
    int particle_id;
    std::vector<std::tuple<float, double, double>> centroid_history;
    std::vector<std::tuple<int, int, float>> events;
};

class Particle {
public:
    int particle_id;
    std::deque<std::tuple<int, int, float>> events;
    std::deque<std::tuple<int, int, float>> recent_events;
    double centroid_x, centroid_y;
    int mass;
    std::deque<std::tuple<float, double, double>> centroid_history;

    Particle(int id, int x, int y, float time) : particle_id(id), centroid_x(x), centroid_y(y), mass(1) {
        events.push_back(std::make_tuple(x, y, time));
        recent_events.push_back(std::make_tuple(x, y, time));
        centroid_history.push_back(std::make_tuple(time, centroid_x, centroid_y));
    }

    void merge(const Particle& other) {
        for (const auto& event : other.events) {
            events.push_back(event);
            recent_events.push_back(event);
        }
        mass += other.mass;
        double total_mass = mass + other.mass;
        centroid_x = (centroid_x * mass + other.centroid_x * other.mass) / total_mass;
        centroid_y = (centroid_y * mass + other.centroid_y * other.mass) / total_mass;
        if (!recent_events.empty()) {
            float time = std::get<2>(recent_events.back());
            centroid_history.push_back(std::make_tuple(time, centroid_x, centroid_y));
        }
    }

    void add_event(int x, int y, float time) {
        events.push_back(std::make_tuple(x, y, time));
        recent_events.push_back(std::make_tuple(x, y, time));
        mass++;
        float cutoff_time = time - 2000.0;
        while (!recent_events.empty() && std::get<2>(recent_events.front()) < cutoff_time) {
            recent_events.pop_front();
        }
        if (!recent_events.empty()) {
            double sum_x = 0, sum_y = 0;
            for (const auto& event : recent_events) {
                sum_x += std::get<0>(event);
                sum_y += std::get<1>(event);
            }
            centroid_x = sum_x / recent_events.size();
            centroid_y = sum_y / recent_events.size();
        }
        centroid_history.push_back(std::make_tuple(time, centroid_x, centroid_y));
    }

    bool is_active(float current_time, int m_threshold) const {
        if (!events.empty() && std::get<2>(events.back()) < current_time - 2000.0) {
            return mass > m_threshold;
        }
        return true;
    }

    bool is_active_final(int m_threshold) const {
        return mass > m_threshold;
    }

    ParticleResult get_result() const {
        ParticleResult result;
        result.particle_id = particle_id;
        result.centroid_history = std::vector<std::tuple<float, double, double>>(centroid_history.begin(), centroid_history.end());
        result.events = std::vector<std::tuple<int, int, float>>(events.begin(), events.end());
        return result;
    }
};

double gaussian_distance(int x1, int y1, float t1, int x2, int y2, float t2, double sigma_x, double sigma_t) {
    double spatial_distance_sq = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2);
    double time_distance_sq = (t1 - t2) * (t1 - t2);
    return std::exp(-spatial_distance_sq / (2 * sigma_x * sigma_x) - time_distance_sq / (2 * sigma_t * sigma_t));
}

void process_event(int x, int y, int polarity, Metavision::Evt3::timestamp_t timestamp, 
                   std::vector<Particle>& particles, int& particle_id_counter,
                   double sigma_x, double sigma_t, double gaussian_threshold, int m_threshold) {
    float time = static_cast<float>(timestamp);

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
        if (found_overlap) break;
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

int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cerr << "Error : need input filename" << std::endl;
        return 1;
    }

    std::ifstream input_file(argv[1], std::ios::in | std::ios::binary);
    if (!input_file.is_open()) {
        std::cerr << "Error : could not open file '" << argv[1] << "' for reading" << std::endl;
        return 1;
    }

    Metadata metadata;
    while (input_file.peek() == '%') {
        std::string header_line;
        std::getline(input_file, header_line);
        if (header_line.substr(0, 11) == "% geometry ") {
            std::istringstream sg(header_line.substr(11));
            std::string sw, sh;
            std::getline(sg, sw, 'x');
            std::getline(sg, sh);
            metadata.sensor_width  = std::stoi(sw);
            metadata.sensor_height = std::stoi(sh);
        }
    }

    const auto tp_start = std::chrono::system_clock::now();
    static constexpr uint32_t WORDS_TO_READ = 1000000;
    std::vector<Metavision::Evt3::RawEvent> buffer_read(WORDS_TO_READ);

    std::vector<Particle> particles;
    int particle_id_counter = 0;
    double sigma_x = 5.0, sigma_t = 200.0, gaussian_threshold = 0.5;
    int m_threshold = 10;

    bool first_time_base_set = false;
    Metavision::Evt3::timestamp_t current_time_base = 0, current_time = 0, current_time_low = 0;
    uint16_t current_ev_addr_y = 0, current_base_x = 0, current_polarity = 0;
    unsigned int n_time_high_loop = 0;

    while (input_file) {
        input_file.read(reinterpret_cast<char *>(buffer_read.data()), WORDS_TO_READ * sizeof(Metavision::Evt3::RawEvent));
        Metavision::Evt3::RawEvent *current_word = buffer_read.data();
        Metavision::Evt3::RawEvent *last_word = current_word + input_file.gcount() / sizeof(Metavision::Evt3::RawEvent);

        for (; !first_time_base_set && current_word != last_word; ++current_word) {
            Metavision::Evt3::EventTypes type = static_cast<Metavision::Evt3::EventTypes>(current_word->type);
            if (type == Metavision::Evt3::EventTypes::EVT_TIME_HIGH) {
                auto *ev_timehigh = reinterpret_cast<Metavision::Evt3::RawEventTime *>(current_word);
                current_time_base = (Metavision::Evt3::timestamp_t(ev_timehigh->time) << 12);
                first_time_base_set = true;
                break;
            }
        }

        for (; current_word != last_word; ++current_word) {
            Metavision::Evt3::EventTypes type = static_cast<Metavision::Evt3::EventTypes>(current_word->type);
            switch (type) {
                case Metavision::Evt3::EventTypes::EVT_ADDR_X: {
                    auto *ev_addr_x = reinterpret_cast<Metavision::Evt3::RawEventXAddr *>(current_word);
                    process_event(ev_addr_x->x, current_ev_addr_y, ev_addr_x->pol, current_time,
                                  particles, particle_id_counter, sigma_x, sigma_t, gaussian_threshold, m_threshold);
                    break;
                }
                case Metavision::Evt3::EventTypes::VECT_12: {
                    uint16_t end = current_base_x + 12;
                    auto *ev_vec_12 = reinterpret_cast<Metavision::Evt3::RawEventVect12 *>(current_word);
                    uint32_t valid = ev_vec_12->valid;
                    for (uint16_t i = current_base_x; i != end; ++i) {
                        if (valid & 0x1) {
                            process_event(i, current_ev_addr_y, current_polarity, current_time,
                                          particles, particle_id_counter, sigma_x, sigma_t, gaussian_threshold, m_threshold);
                        }
                        valid >>= 1;
                    }
                    current_base_x = end;
                    break;
                }
                case Metavision::Evt3::EventTypes::VECT_8: {
                    uint16_t end = current_base_x + 8;
                    auto *ev_vec_8 = reinterpret_cast<Metavision::Evt3::RawEventVect8 *>(current_word);
                    uint32_t valid = ev_vec_8->valid;
                    for (uint16_t i = current_base_x; i != end; ++i) {
                        if (valid & 0x1) {
                            process_event(i, current_ev_addr_y, current_polarity, current_time,
                                          particles, particle_id_counter, sigma_x, sigma_t, gaussian_threshold, m_threshold);
                        }
                        valid >>= 1;
                    }
                    current_base_x = end;
                    break;
                }
                case Metavision::Evt3::EventTypes::EVT_ADDR_Y: {
                    auto *ev_addr_y = reinterpret_cast<Metavision::Evt3::RawEventY *>(current_word);
                    current_ev_addr_y = ev_addr_y->y;
                    break;
                }
                case Metavision::Evt3::EventTypes::VECT_BASE_X: {
                    auto *ev_xbase = reinterpret_cast<Metavision::Evt3::RawEventXBase *>(current_word);
                    current_polarity = ev_xbase->pol;
                    current_base_x = ev_xbase->x;
                    break;
                }
                case Metavision::Evt3::EventTypes::EVT_TIME_HIGH: {
                    static constexpr Metavision::Evt3::timestamp_t MaxTimestampBase = ((Metavision::Evt3::timestamp_t(1) << 12) - 1) << 12;
                    static constexpr Metavision::Evt3::timestamp_t TimeLoop = MaxTimestampBase + (1 << 12);
                    static constexpr Metavision::Evt3::timestamp_t LoopThreshold = (10 << 12);

                    auto *ev_timehigh = reinterpret_cast<Metavision::Evt3::RawEventTime *>(current_word);
                    Metavision::Evt3::timestamp_t new_time_base = (Metavision::Evt3::timestamp_t(ev_timehigh->time) << 12);
                    new_time_base += n_time_high_loop * TimeLoop;

                    if ((current_time_base > new_time_base) &&
                        (current_time_base - new_time_base >= MaxTimestampBase - LoopThreshold)) {
                        new_time_base += TimeLoop;
                        ++n_time_high_loop;
                    }

                    current_time_base = new_time_base;
                    current_time = current_time_base;
                    break;
                }
                case Metavision::Evt3::EventTypes::EVT_TIME_LOW: {
                    auto *ev_timelow = reinterpret_cast<Metavision::Evt3::RawEventTime *>(current_word);
                    current_time_low = ev_timelow->time;
                    current_time = current_time_base + current_time_low;
                    break;
                }
                default:
                    break;
            }
        }
    }

    const auto tp_end = std::chrono::system_clock::now();
    const double duration_s = std::chrono::duration_cast<std::chrono::microseconds>(tp_end - tp_start).count() / 1e6;

    std::vector<ParticleResult> results;
    for (const auto& particle : particles) {
        results.push_back(particle.get_result());
    }
    std::cout << "Processed in " << duration_s << " s" << std::endl;

    return 0;
}