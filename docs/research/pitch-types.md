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
| 슈트 | 던지는 팔 쪽으로 강하게 파고드는 패스트볼 변형 (일본). **2026-10-06 뺌** (KAL: 논란이 있는 공) | [Wikibooks](https://ja.wikibooks.org/wiki/%E9%87%8E%E7%90%83/%E5%A4%89%E5%8C%96%E7%90%83/%E3%82%B7%E3%83%A5%E3%83%BC%E3%83%88) |
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
