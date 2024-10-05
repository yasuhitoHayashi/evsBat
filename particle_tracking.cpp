#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <deque>
#include <vector>
#include <tuple>
#include <cmath>
#include <algorithm>
#include <limits>

// 粒子追跡の結果を格納するstruct
struct ParticleResult {
    int particle_id; // 粒子ID
    std::vector<std::tuple<float, double, double>> centroid_history;  // (time, centroid_x, centroid_y)
    std::vector<std::tuple<int, int, float>> events;  // イベントのリスト(x, y, time)
};

// 粒子を追跡・管理するクラス
class Particle {
public:
    int particle_id; // 粒子ID
    std::deque<std::tuple<int, int, float>> events;  // (x, y, time)イベントのリスト
    std::deque<std::tuple<int, int, float>> recent_events;  // 重心計算用の最新イベントリスト
    double centroid_x, centroid_y; // 粒子の現在の重心座標
    int mass; // 粒子に属するイベントの数
    std::deque<std::tuple<float, double, double>> centroid_history;  // 重心の履歴のリスト(time, centroid_x, centroid_y)

    // コンストラクタ。Particleクラスの初期化。粒子を新しく生成するときにこれを呼び出し、初期イベントを追加する。
    Particle(int id, int x, int y, float time) : particle_id(id), centroid_x(x), centroid_y(y), mass(1) {
        events.push_back(std::make_tuple(x, y, time)); // 最初のイベントを追加
        recent_events.push_back(std::make_tuple(x, y, time));  // 最新イベントに追加
        centroid_history.push_back(std::make_tuple(time, centroid_x, centroid_y)); // 重心履歴に追加
    }

    // 他の粒子を対象粒子にマージする関数。this粒子にother粒子のイベントを追加し、質量を統合する。
    void merge(const Particle& other) {
        // 他の粒子のイベントを全て追加
        for (const auto& event : other.events) {
            events.push_back(event);
            recent_events.push_back(event);  // recent_eventsにも追加
        }

        // 質量の統合
        mass += other.mass;

        // 重心の再計算（質量で重み付けした座標平均）
        double total_mass = mass + other.mass;
        centroid_x = (centroid_x * mass + other.centroid_x * other.mass) / total_mass;
        centroid_y = (centroid_y * mass + other.centroid_y * other.mass) / total_mass;

        // 重心の履歴を更新
        if (!recent_events.empty()) {
            float time = std::get<2>(recent_events.back());
            centroid_history.push_back(std::make_tuple(time, centroid_x, centroid_y));
        }
    }

    // 粒子に新しいイベントを追加する関数。重心の計算と履歴の更新も行う。
    void add_event(int x, int y, float time) {
        events.push_back(std::make_tuple(x, y, time));
        recent_events.push_back(std::make_tuple(x, y, time));  // recent_eventsにも追加
        mass++; // 質量を増やす

        // 古いイベントの削除 (2000usより古いイベントを削除)
        float cutoff_time = time - 2000.0;
        while (!recent_events.empty() && std::get<2>(recent_events.front()) < cutoff_time) {
            recent_events.pop_front();
        }

        // 重心の再計算。すべてのイベントのx, y座標を合計し、それぞれ平均を取る。
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

    // 粒子がアクティブかどうかを時間と質量に基づいてチェックする関数
    bool is_active(float current_time, int m_threshold) const {
        if (!events.empty() && std::get<2>(events.back()) < current_time - 2000.0) {
            return mass > m_threshold;  // 直近2000us以内にイベントがない場合は、質量が閾値より大きいかどうかを返す
        }
        return true;  // 直近2000us以内にイベントがある場合は常にアクティブ
    }

    // 質量だけでの判断を行う最終的なアクティブチェック関数(最後の時間ステップで、小さい粒子を削除するため)
    bool is_active_final(int m_threshold) const {
        return mass > m_threshold;
    }

    // C++のParticleResultをpythonに返すため、ParticleResultオブジェクトを作成して返す関数
    ParticleResult get_result() const {
        ParticleResult result;
        result.particle_id = particle_id;
        result.centroid_history = std::vector<std::tuple<float, double, double>>(centroid_history.begin(), centroid_history.end());
        result.events = std::vector<std::tuple<int, int, float>>(events.begin(), events.end());
        return result;
    }
};

// ガウス分布による距離計算。2つのイベント間の空間的な距離(x, y)と時間的な距離(t)を計算し、ガウス分布に基づくスコアを返す。
// sigma_xは空間的なガウス分布の標準偏差、sigma_tは時間的なガウス分布の標準偏差。
double gaussian_distance(int x1, int y1, float t1, int x2, int y2, float t2, double sigma_x, double sigma_t) {
    double spatial_distance_sq = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2);  // 空間的な距離の2乗
    double time_distance_sq = (t1 - t2) * (t1 - t2);  // 時間的な距離の2乗
    return std::exp(-spatial_distance_sq / (2 * sigma_x * sigma_x) - time_distance_sq / (2 * sigma_t * sigma_t));  // ガウス分布に基づくスコア。1に近いほど、時空間的にイベントが近接している。
}

// イベントベースの粒子追跡アルゴリズム。イベントデータを受け取り、粒子を追跡して、最終的な粒子リストを返す。
std::vector<ParticleResult> track_particles_cpp(const std::vector<std::tuple<int, int, float>>& data, double sigma_x, double sigma_t, double gaussian_threshold, int m_threshold) {
    // 空の粒子ベクトルを作成
    std::vector<Particle> particles;
    int particle_id_counter = 0; // 粒子idのカウンターリセット

    // データ内の各イベントに対して粒子追跡を実行
    for (const auto& event : data) {
        // イベントのx, y, timeを取得
        int x = std::get<0>(event);
        int y = std::get<1>(event);
        float time = std::get<2>(event);

        // 既存の粒子に新たなイベントを追加するかをチェック
        bool found_overlap = false;
        size_t overlapping_particle_index = std::numeric_limits<size_t>::max(); //既存粒子との重なりがある場合、インデックスを格納

        // すべての粒子(を構成するイベント)と新たなイベントの距離を計算し、重なりがあるかどうかをチェック
        for (size_t i = 0; i < particles.size(); ++i) {
            Particle& particle = particles[i];

            // 粒子を構成するイベントのうち最新のイベントリストをループし、新しいイベントとの距離を計算
            for (const auto& recent_event : particle.recent_events) {
                // ガウス分布に基づいた距離を計算
                double gaussian_score = gaussian_distance(x, y, time, std::get<0>(recent_event), std::get<1>(recent_event), std::get<2>(recent_event), sigma_x, sigma_t);

                // スコアが閾値を超えた場合にイベントのインデックスを追加
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

        // もし、どの粒子とも重なりがない場合、新しい粒子を作成
        if (!found_overlap) {
            particle_id_counter++; // 粒子IDに1を追加
            Particle new_particle(particle_id_counter, x, y, time);
            particles.push_back(new_particle);
        // 重なりがある場合、重なりがある粒子をマージ
        } else if (overlapping_particle_index != std::numeric_limits<size_t>::max()) {
            // あるイベントが複数の粒子と重なっている場合、2つの粒子の直近のイベントを比較し、重なりがあるかどうかをチェック。閾値を超えた場合、粒子をマージ
            for (size_t i = 0; i < particles.size(); ++i) {
                if (i != overlapping_particle_index) {
                    Particle& particle = particles[i];

                    // ガウス分布に基づく距離計算で、同じ条件で2つの粒子が重なっているかチェック
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
                            // 粒子をマージ
                            particles[overlapping_particle_index].merge(particle);
                            particles.erase(particles.begin() + i);  // Merge後、消す
                            break;
                        }
                    }
                }
            }
        }

        // 最後のイベントから2000ms以上経過し、質量が閾値より小さい場合、粒子を削除
        particles.erase(std::remove_if(particles.begin(), particles.end(),
            [time, m_threshold](const Particle& p) { return !p.is_active(time, m_threshold); }), particles.end());
    }

    // 最後の時間ステップで、質量が閾値より小さい粒子を削除
    particles.erase(std::remove_if(particles.begin(), particles.end(),
        [m_threshold](const Particle& p) { return !p.is_active_final(m_threshold); }), particles.end());

    // 結果を返す
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