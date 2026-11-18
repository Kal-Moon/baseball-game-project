## 직접 플레이 숫자 (docs/game-design.md 5.0절, simulation/direct_play_sim.py와 같은 값)
## 모두 보통 유저가 직접 쳤을 때 능력치 +20 효과 = 자동 경기 +20 효과가 되도록 맞춘 조정값.
extends RefCounted

const GRADES := ["too", "near", "good", "perfect"]          # 너무 · 빠름/늦음 · 좋음 · 완벽
const RESULTS := ["whiff", "foul", "weak", "normal", "strong"]

const P := {
	"aim_zone": 0.47, "sigma": 0.42, "miss": 0.03, "miss_center": 0.85, "body_x": -2.13,
	"out_zone_penalty": 0.6, "out_zone_whiff": 0.24,
	# 타구 질 → [안타 확률, 그중 2루타, 3루타, 홈런 확률(타구 전체 기준)]
	"weak": [0.12, 0.05, 0.00, 0.000],
	"normal": [0.362, 0.20, 0.02, 0.011],
	"strong": [0.62, 0.32, 0.03, 0.140],
}

## 타이밍 단계별 [헛스윙, 파울, 약한, 보통, 강한] (존 안 공). SKILL_BLEND 적용 전 원래 표.
const BASE_OUTCOME := {
	"too": [0.45, 0.42, 0.13, 0.00, 0.00],
	"near": [0.06, 0.52, 0.24, 0.18, 0.00],
	"good": [0.00, 0.40, 0.14, 0.32, 0.14],
	"perfect": [0.00, 0.22, 0.05, 0.25, 0.48],
}

const SKILL_BLEND := 0.35     # 타이밍 단계 결과 차이를 원래의 35%로 (5.6절)
const COMPAT_EFFECT := 0.4    # 코스·스윙 궁합 효과 40%

## 유저 세 단계 (5.5절, 타이밍 분포는 가정 → 시험판 기록으로 고침)
const USERS := {
	"서툰": {"zone_swing": 0.60, "chase": 0.40, "timing": [0.40, 0.35, 0.20, 0.05], "compat": [0.25, 0.45, 0.30]},
	"보통": {"zone_swing": 0.667, "chase": 0.305, "timing": [0.25, 0.35, 0.30, 0.10], "compat": [0.40, 0.40, 0.20]},
	"잘함": {"zone_swing": 0.72, "chase": 0.22, "timing": [0.15, 0.30, 0.35, 0.20], "compat": [0.55, 0.35, 0.10]},
}

const EYE := {"coef": 0.0025, "cap_slow": 0.10, "cap_fast": -0.05, "chase": 2.0, "timing": 0.5}        # 5.7
const VEL := {"eye_w": 0.1, "late": 0.0035, "whiff": 2.0, "cap_pos": 20, "cap_neg": -40, "neg_scale": 1.0}  # 5.10
const CON := {"coef": 0.016, "brk_weight": 0.25, "stuff_weight": 0.16, "cap_pos": 40, "cap_neg": -20,
	"to_foul": 0.7, "upgrade": 2.0, "neg_whiff": 0.55, "neg_down": 2.0}                                  # 5.8
const BRK := {"coef": 0.008, "cap_pos": 20, "cap_neg": -40, "neg_scale": 0.4}                        # 5.8
const POW := {"stuff_weight": 0.3, "hr": 0.008, "up": 0.01, "neg_up": 1.7, "cap_pos": 40, "cap_neg": -20}  # 5.9
const TIMING_W := [0.0, 0.3, 0.7, 1.0]
const STF := {"coef": 0.004, "cap_pos": 20, "cap_neg": -40, "neg_scale": 0.3}                        # 5.9
const CTL := {"circle": 0.019, "miss": 0.015, "body": 0.0135, "body_neg": 0.012, "neg_scale": 0.6,
	"cap_pos": 20, "cap_neg": -40}                                                                   # 5.11
