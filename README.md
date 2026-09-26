# 야구 게임 프로젝트

직접 치고 던지는 2D 모바일(안드로이드) 야구 게임. 선수를 키우고 그 선수들로 팀을 운영하는 구조예요.

- 기획: KAL
- 코드·시뮬레이션·문서 정리: Claude
- 엔진: Godot (예정)

## 폴더 구성

| 경로 | 내용 |
| --- | --- |
| `docs/game-design.md` | 기획 문서 (큰 틀, 첫 버전 범위, 시뮬레이션 결과, 보류 목록, 참고 자료) |
| `docs/dev-machine-spec.md` | 개발 PC 사양과 개발 가능 범위 |
| `docs/mockups/` | 모바일 가로 화면 예시 (임시 그림) |
| `simulation/baseball_sim.py` | 밸런스 시뮬레이터 (파이썬) |
| `CHANGELOG.md` | 작업 기록 |

## 시뮬레이터 실행

```bash
cd simulation
python3 baseball_sim.py
```

파이썬 3.9 이상, 외부 라이브러리 없음. 전체 실험은 1~2분 정도 걸려요. 난이도(능력치 영향력)는 파일 위쪽의 `SCALE` 값으로 조정해요.
