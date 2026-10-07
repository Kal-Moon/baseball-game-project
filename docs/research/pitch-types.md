# 구종 종류 조사 자료

> 조사일: 2026-10-05 · 정리: Claude
> 용도: 투수 구종 목록(기본 구종·특수 구종)을 정한 근거. 결정 내용은 `docs/game-design.md` 2.3절 "투수 구종".
> 주의: mlb.com·fangraphs.com 등이 막혀 있어 대부분 **검색 요약**으로만 확인함. 원문을 확인하지 못한 수치는 그렇게 적음.

---

## 1. MLB 공식 구종 분류 (Statcast)

MLB 홈페이지 Pitch Types 목록 (KAL 스크린샷으로 확인): **14가지**

| 코드 | 구종 | 우리 게임 |
| --- | --- | --- |
| FF | Four-Seam Fastball | 포심 (기본) |
| SI | Sinker | 싱커 (기본, 투심 포함) |
| FC | Cutter | 커터 (기본) |
| SL | Slider | 슬라이더 (기본) |
| ST | Sweeper | 스위퍼 (기본) |
| SV | Slurve | 슬러브 (특수) |
| CU | Curveball | 커브 (기본) |
| KC | Knuckle-curve | 너클커브 (기본) |
| CH | Changeup | 체인지업·서클체인지업으로 나눔 (기본) |
| FS | Splitter | 스플리터 (기본) |
| FO | Forkball | 포크볼 (기본) |
| SC | Screwball | 스크류볼 (특수) |
| EP | Eephus | 이퓨스 (특수) |
| KN | Knuckleball | 넣지 않음 |

- MLB는 투심을 따로 세지 않고 싱커(SI)로, 서클체인지업도 체인지업(CH)으로 셈 ([Daktronics](https://www.daktronics.com/en-us/support/kb/000001823)). 우리 게임은 투심을 싱커에 묶고(KAL, 표기 "싱커"), 서클체인지업은 움직임이 달라서 나눔.
- 스위퍼(ST)·슬러브(SV)는 2023년 추가된 분류라고 함 ([MLB.com 스위퍼](https://www.mlb.com/glossary/pitch-types/sweeper), [MLB.com 슬러브](https://www.mlb.com/glossary/pitch-types/slurve), 검색 요약. 원문은 접속이 막혀 확인 못 함).
- 2026-10-05 정정: 처음 정리 때 MLB가 따로 세는 너클커브·슬러브·포크볼을 그 사실을 말하지 않고 합쳤음. 근거를 골라 쓴 잘못이라 다시 나눔.

## 2. 구종 사용 비율

- **MLB 2025**: 포심 47.9%, 슬라이더 22.4%, 체인지업 10.0%, 커브 8.6%, 커터 7.6%, 스위퍼 7.6%, 스플리터 3.6% ([RotoWire](https://www.rotowire.com/baseball/article/mlb-pitch-speed-and-usage-2002-to-2025-94262)). 싱커 전체 비율은 못 찾음 (반대손 타자 상대 9.7%만 확인).
- **KBO**: 포심 42.2%, 투심 8.8%, 슬라이더 23.4%. 2015년은 포심 50.9%, 투심 3.3% ([시사IN](https://www.sisain.co.kr/news/articleView.html?idxno=48258)). **몇 년도 자료인지 확인 못 함.**
- 너클커브·슬러브·포크볼의 사용 비율은 확인 못 함.

## 3. 구종별 자료

| 구종 | 내용 | 출처 |
| --- | --- | --- |
| 투심·싱커 | 옆으로 휘는 쪽을 투심, 아래로 가라앉는 쪽을 싱커라 부르는 경향. 같은 뜻으로도 씀. 국내 대표 싱커 투수 정대현 | [many-information](https://many-information.com/baseball-sinker-two-seam-grip-movement-guide/) |
| 슈트 (넣지 않음, KAL) | 던지는 팔 쪽으로 강하게 파고드는 패스트볼 변형 (일본) | [Wikibooks](https://ja.wikibooks.org/wiki/%E9%87%8E%E7%90%83/%E5%A4%89%E5%8C%96%E7%90%83/%E3%82%B7%E3%83%A5%E3%83%BC%E3%83%88) |
| 스플링커 | 스플리터 그립으로 세게 던져 싱커처럼 팔 쪽으로 휘며 떨어짐. 조안 듀란 약 96~97mph, 약 25~26인치 낙차, 팔 쪽 13~17인치. Statcast는 스플리터 → 싱커로 분류 (따로 분류 없음) | [MLB.com](https://www.mlb.com/news/jhoan-duran-on-his-unique-splinker-pitch), [Boston Globe](https://www.bostonglobe.com/2022/09/03/sports/twins-jhoan-duran-is-fast-becoming-concern-major-league-hitters/) |
| 고속 슬라이더(슬러터) | 보통 슬라이더보다 빠르고 덜 휨 (마쓰자카). 슬러터는 커터와 슬라이더 사이 | [rere.jp](https://www.rere.jp/358169/), [나무위키](https://namu.wiki/w/%EC%95%BC%EA%B5%AC%EC%9D%98%20%EA%B5%AC%EC%A2%85) |
| 종슬라이더 | 아래로 떨어지는 슬라이더 (마쓰자카, 이마이). 포크보다 미끄러지듯 떨어짐 | [rere.jp](https://www.rere.jp/358169/) |
| 파워커브 | 보통 커브보다 빠르고, 옆으로 덜 휘고 곧게 떨어짐 (김상엽, 임정우 등) | [위키백과](https://ko.wikipedia.org/wiki/%ED%8C%8C%EC%9B%8C%EC%BB%A4%EB%B8%8C) |
| 너클커브 | 잡는 법만 다르고 구속·움직임은 커브와 거의 같음. 회전수가 많다고 함 | [다음](https://v.daum.net/v/kyxzt7Io7U) |
| 12-6 커브·슬러브 | 커브가 휘는 각도 차이 (세로로 / 옆으로 더). 파워프로도 커브·드롭·슬러브를 각도로 나눔 | [Game8 파워프로](https://kamigame.jp/pawapuro2022/page/208592516688182350.html) |
| 서클체인지업 | 투수의 팔 쪽으로 휨 (KAL). 스크류볼과 휘는 방향·속도가 비슷하고 팔을 덜 비틀어서 스크류볼을 대신하게 됨 | [FanGraphs](https://blogs.fangraphs.com/searching-for-the-modern-screwball/) (검색 요약) |
| 스크류볼 | 커브와 반대 방향으로 휨. 옛 기록 평균 69.2mph로 서클체인지업(85.1mph)보다 훨씬 느림 | [FanGraphs](https://blogs.fangraphs.com/searching-for-the-modern-screwball/) (검색 요약) |
| 킥 체인지업 | 가운뎃손가락을 세워 차듯이 놓아 회전을 줄임. 약 900rpm, 수직 무브먼트 거의 0(스플리터와 비슷), 옆 약 10인치, 구속은 고속 슬라이더 수준. KAL 비교표의 "최대 25cm 이상 낙차"는 확인 못 함 | [Yahoo Sports](https://sports.yahoo.com/mlb/article/the-birth-of-mlbs-newest-pitch-the-kick-change-120819082.html), [Lookout Landing](https://www.lookoutlanding.com/2025/2/28/24367452/what-the-kick-change-is-pitch-of-2025-andres-munoz-brian-bannister-supination-pronation) |
| 벌칸 체인지업 | 가운뎃손가락과 약지 사이로 잡음. 스플리터·포크볼과 비슷하게 떨어짐 | [Wikipedia](https://en.wikipedia.org/wiki/Vulcan_changeup) (검색 요약) |
| 팜볼 | 손바닥으로 밀어 회전이 적고 흔들리며 가라앉음. 옆으로 거의 안 휘고 포물선 꼭대기에서 떨어짐. 무기는 패스트볼과의 속도 차이. 잡는 법이 불안정해 제구가 어려움. 지금은 드묾 (도코다 히로키) | [コトバンク](https://kotobank.jp/word/%E3%81%B1%E3%83%BC%E3%82%80%E3%81%BC%E3%83%BC%E3%82%8B-3215865), [baseball-jiten](https://baseball-jiten.com/terms/palmball/), [나무위키](https://en.namu.wiki/w/%ED%8C%9C%EB%B3%BC), [FMV](https://fmv-mypage.fmworld.net/fmv-sports/post-14887/) |
| 돌직구 (오승환) | 회전수 분당 약 2,875회, 낙차가 다른 투수 평균보다 작음 → 구위·패스트볼 무브먼트 스킬로 처리 | [다음](https://v.daum.net/v/M0N76Tc5JD) |
| 뱀직구 (임창용) | 사이드암의 옆 회전으로 꿈틀거리며 휨 → 투구폼으로 처리 (보류) | [스포츠경향](https://sports.khan.co.kr/article/201404220700013) |

## 4. 다른 게임

- 컴프야: 포심, 체인지업, 슬라이더, 커브, 커터, 스플리터, 포크, 싱커, 투심, 써클체인지업 ([컴프야 커뮤니티](https://cpbv-community.com2us.com/board/11/260070))
- 파워프로: 변화구를 방향(각도)·변화량·구속·예리함 값으로 정의 (예: H슈트 각도 +90°, SFF 각도 0°) ([Game8](https://kamigame.jp/pawapuro2022/page/208592516688182350.html))

## 5. 포크볼·스플리터 속도와 회전 (2026-10-05 추가)

- NPB 포크볼 평균 약 135km/h, 스플리터 약 138km/h. 패스트볼 대비 스플리터 약 5~12km/h, 포크볼 약 8~18km/h 느림 ([halftime-media](https://halftime-media.com/sports-market/baseball-split/), [baseball-jiten](https://baseball-jiten.com/columns/fork-vs-split/)). 연도 확인 못 함.
- 홈까지 스플리터 약 20바퀴, 포크볼 약 10바퀴 ([halftime-media](https://halftime-media.com/sports-market/baseball-split/)). MLB 스플리터 평균 1,302rpm, 사사키 519rpm ([MLB Korea](https://www.mlbkor.com/news/articleView.html?idxno=20644)).
- KAL 자료(출처 표시: mlbkor 등): 포심 2,200~2,500rpm, 슬라이더·커브 2,300~2,800, 스플리터 1,000~1,400, 포크볼 300~600, 너클볼 0~150. 포크볼 수치는 따로 확인 못 함.
- 처음 초안에서 포크볼 비율을 0.87로 너무 느리게 잡았다가 0.91로 고침 (KAL 지적: 포크볼은 그렇게 느린 공이 아님).

## 6. 구종별 평균 구속·무브먼트

- 2025 MLB 평균 구속: 포심 94.0, 커터 89.4, 스플리터 86.4, 체인지업 85.9, 슬라이더 84.8, 커브 80.5mph ([RotoWire](https://www.rotowire.com/baseball/article/mlb-pitch-speed-and-usage-2002-to-2025-94262)). 싱커·스위퍼·슬러브·너클커브·포크볼의 2025 평균은 못 찾음.
- 무브먼트(IVB 기준): [Baseball Scouter](https://baseballscouter.com/vertical-vs-horizontal-pitch-break/), [Optimum Athletes](https://www.optimumathletes.com/blog/pitch-metrics-horizontal-and-vertical-break). 같은 검색에 기준이 다른 표가 섞여 나와 그 표는 쓰지 않음.

## 7. 투수별 구종 수 (2025 MLB, Baseball Savant 직접 계산)

> 조사일: 2026-10-07. 정규시즌. Savant 구종 사용 비율 순위표(`leaderboard/pitch-arsenals?year=2025&type=n_&csv=true`)와 투수별 투구 수(statcast_search CSV)를 합침.
> 선발·불펜은 공식 기록이 아니라 **1회에 던진 공의 비율**로 나눔: 선발 = 1,500구 이상 + 1회 투구 15% 이상, 불펜 = 600구 이상 + 1회 투구 2% 미만.
> 구종 수 = 그 구종을 전체 투구의 10%(또는 5%) 이상 던진 수. 10%는 정한 기준이고 근거 자료는 없음.

| | 투수 수 | 10% 이상 구종 수 | 5% 이상 구종 수 |
| --- | --- | --- | --- |
| 선발 | 131 | 평균 3.9 (2개 8 / 3개 38 / 4개 53 / 5개 27 / 6개 5) | 평균 4.7 (보통 5) |
| 불펜 | 170 | 평균 3.0 (1개 1 / 2개 48 / 3개 77 / 4개 37 / 5개 7) | 평균 3.4 (보통 3) |
| 전체 600구 이상 | 437 | 평균 3.5 (1개 1 / 2개 64 / 3개 158 / 4개 151 / 5개 55 / 6개 7 / 7개 1) | 평균 4.1 |

- 구종별로 10% 이상 던지는 투수 비율: 선발 포심 91%, 싱커 60%, 슬라이더 53%, 체인지업 52%, 커브 51%, 커터 37%, 스위퍼 27%, 스플리터 15%, 슬러브 2%. 불펜 포심 78%, 슬라이더 57%, 싱커 50%, 스위퍼 31%, 체인지업 26%, 커터 21%, 커브 20%, 스플리터 16%, 슬러브 1%.
- 포심 또는 싱커를 10% 이상: 선발 100%, 불펜 98%. **패스트볼 계열(포심·싱커·커터)이 하나도 없는 투수는 0명.** 포심·싱커 둘 다 10% 미만인 투수는 437명 중 7명(1.6%)이고 모두 커터가 주 패스트볼: 클라세(커터 69%·슬라이더 30%, 포심·싱커 없음), 애시크래프트(커터 54%·슬라이더 46%, 없음), 플루하티(커터 58%·스위퍼 42%, 없음), 잰슨(커터 81%·싱커 9%), 번스(커터 55%·싱커 10% 미만), 스펜스, 슈미트.
- 2026-10-07 정정: 처음에 "커터만 있는 투수는 없다"고 잘못 말함 (포심·싱커·커터가 모두 10% 미만인 투수가 0명이라는 결과를 잘못 읽음). 위 7명이 있음.
- 구종 수별 포심 평균 구속(포심 100구 이상): 선발 2개 96.0mph(8명) / 3개 93.6 / 4개 93.8 / 5개 93.8 / 6개 94.7(5명). 불펜 2개 95.9 / 3개 95.6 / 4개 94.9. 구종 수별 피xwOBA(낮을수록 좋음): 선발 2개 .303 / 3개 .314 / 4개 .319 / 5개 .325, 불펜 2개 .287 / 3개 .300 / 4개 .307. 구종이 적은 투수가 공이 더 좋은 쪽이지만, 원인은 반대일 수 있음 (공이 좋아서 적은 구종으로 버팀).
- 투피치 예: 선발 딜런 시즈(포심·슬라이더), 케빈 가우스먼(포심·스플리터), 스펜서 스트라이더(포심·슬라이더), 크리스 세일(포심·슬라이더). 불펜 데빈 윌리엄스(포심·체인지업), 캐이드 스미스(포심·스플리터).
- 한계: 순위표의 구종 칸은 FF·SI·FC·SL·CH·CU·FS·KN·ST·SV 10개뿐. 너클커브는 커브에 섞인 것으로 보이지만 확인 못 함. **포크볼(FO) 칸이 없어서** 센가 고다이는 포심·커터 투피치로 잡힘 (실제로는 포크볼도 주무기). 스크류볼·이퓨스·슬로우 커브도 빠짐.
- 한국(KBO)·일본(NPB) 구종 수와 구종별 비율은 아직 조사 안 함.
- 다른 게임: MLB The Show 투수 육성 모드(RTTS)는 구종 3개로 시작해 최대 5개. 늘리는 방법은 시리즈마다 바뀜 ([TrueAchievements](https://www.trueachievements.com/game/MLB-The-Show-21/walkthrough/3), [RealSport101](https://realsport101.com/mlb-the-show/mlb-the-show-22-how-to-change-pitches-rtts-diamond-dynasty-road-to-the-show-ballplayer/)). 파워프로는 특별한 변화구(오리지널 변화구)를 이벤트로 얻음 ([Game8](https://game8.jp/pawapuro2026-2027/791323)). 컴프야의 구종 수 규칙은 못 찾음.


## 8. KBO 구종 구사율 (2026-10-07 조사)

> 스탯티즈(`www.statiz.co.kr`)는 기록 페이지가 모두 **로그인 필요**라 직접 받지 못함. 시사IN 기사는 접속이 막혀 **웹 검색 요약으로만** 확인 (원문 확인 못 함). 아래는 **공 단위 구사율**(전체 투구 중 그 구종 비율)이고, 게임에 필요한 "그 구종을 가진 투수 비율"(7장 같은 투수 단위)은 아님.

| 구종 | KBO | 연도 | 출처 |
| --- | --- | --- | --- |
| 패스트볼 전체 | 51.0% | 2022 | 시사IN 2022-08-28 |
| 포심 | 42.2% (2015년 50.9%) | 2022 | 같은 기사 |
| 투심 (= 싱커) | 8.8% (2015년 3.3%) | 2022 | 같은 기사 |
| 슬라이더 | 23.4% (2022), **21.4%** (2025, 패스트볼 빼고 가장 많음) | 2022·2025 | 같은 기사, 시사IN 2026 |
| 스플리터 | 6.4% ("주요 구종 중 가장 낮음") | 2022 | 같은 기사 |
| 커브 | 9.1% (검색 요약에 나왔으나 어느 기사·연도인지 확실하지 않음) | ? | - |
| 스위퍼 | **0.7%** (던진 투수 22명) → 2026년 5월 4일까지 **4.3%** (38명, 그중 80.1%를 외국인 투수가 던짐, 내국인 20명) | 2025·2026 | 시사IN 2026 |
| 사이드암 체인지업 | 21.3% (2015년 10.3%) | 2022 | 시사IN 2022-08-28 |
| 체인지업·포크볼·커터 (전체) | 확인 못 함 | - | - |

- 출처: [한국 투수들이 선호하는 구종은? – 시사IN](https://www.sisain.co.kr/news/articleView.html?idxno=48258) (2022-08-28), [KBO에 덜 떨어지고 더 휘는 '스위퍼' 바람이 분다 – 시사IN](https://www.sisain.co.kr/news/articleView.html?idxno=57844) (2026). 원 자료는 스탯티즈로 보임 (확인 못 함).
- MLB 2025 공 단위 구사율과 비교 (RotoWire, 2장): 슬라이더 22.4%, 체인지업 10.0%, 커브 8.6%, 커터 7.6%, **스위퍼 7.6%**, 스플리터 3.6%. 연도가 다른 KBO 값(2022)과 섞어 비교하면 안 되는 것에 주의.
  - 같은 연도(2025)로 비교 가능한 것: 슬라이더 KBO 21.4% vs MLB 22.4% (비슷), **스위퍼 KBO 0.7% vs MLB 7.6%** (KBO가 약 1/10).
  - KAL 예상("한국은 슬라이더·스위퍼 선호")과 다른 점: 2025년까지 한국은 스위퍼가 아주 적었음. 2026년에 외국인 투수 중심으로 늘어나는 중.
- 일본(NPB) 참고: Japan Baseball Lab 추정 선발 공 단위 구사율 — 포심 35~42%, **스플리터·포크볼 14~18%**(MLB 4~6%), 슬라이더 12~16%, 커브 10~14%, 체인지업 6~10%, 싱커·투심 5~8%, 커터 3~6%. NPB 트랙맨 2019~2023 일부 구장 기준의 대략값 ([Japan Baseball Lab](https://japanbaseballlab.com/npb-pitch-mix-vs-mlb-statcast/), 원 자료 확인 못 함). 나라 단위로 넓힐 때 참고.
- 구종별로 10% 이상 던지는 투수 비율 (2025 MLB, 600구 이상 437명, statcast_search 구종별 CSV로 다시 계산해 너클커브·포크볼 등도 포함): 포심 85.4%, 슬라이더 54.7%, 싱커 53.8%, 체인지업 41.6%, 스위퍼 31.6%, 커터 30.0%, 커브 29.1%, 스플리터 14.6%, 너클커브 7.3%, 슬러브 1.6%, 포크볼 0.5%(2명), 스크류볼·슬로우 커브·이퓨스 0명. 서클체인지업은 체인지업(CH)에 섞여 따로 셀 수 없음.

