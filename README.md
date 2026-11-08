# voicescroll-claude-plugin

VoiceScroll 의 Claude 플러그인 묶음(VS-0592)이다. Claude 로 쓴 대본을 링크 하나로 VoiceScroll 앱에 넘긴다.
서버가 없다. 스킬의 코드는 Claude 가 코드를 실행하는 자리(claude.ai 코드 샌드박스 · Claude Code 의 컴퓨터)에서
표준 라이브러리만으로 링크를 만든다. 코드는 파일이 아니라 각 `SKILL.md` 끝의 python 블록에 있다(아래 «코드 자리»).

이 파일이 이 저장소의 정본이다. 사용자가 보는 설명은 `voicescroll/README.md`(디렉터리 목록에 실린다)다.

## 꼴

```
voicescroll/                      플러그인 폴더 — 설치하는 사람이 받는 것은 이 폴더뿐이다
  .claude-plugin/plugin.json      name "voicescroll" — 출시 뒤 바꾸지 않는다(설치 이름)
  .claude-plugin/icon.png         목록 아이콘 — iOS AppIcon 1024 · plugin.json `icon` 이 가리킨다
  README.md                       디렉터리 목록의 설명(40 낱말 이상 · 무엇을 보내는지)
  LICENSE                         MIT
  skills/
    script-format/SKILL.md        대본 다듬기 — 말하지 않는 글을 지시문 괄호에 넣고 앱처럼 검사한다 · 끝에 검사 코드
    script-link/SKILL.md          링크 꼴 v1 링크 만들기 · 끝에 링크 코드
    reading-time/SKILL.md         읽는 시간 어림 · 시간에 맞는 길이 · 끝에 세기 코드
LICENSE                           voicescroll/LICENSE 와 같은 MIT — GitHub 가 저장소의 라이선스로 읽는다
e2e/                              플러그인 밖 — Claude Code 끝에서 끝 시험(링크 옮겨 적기 · 스킬 고르기)
  run.sh                          이 플러그인만 실은 claude -p 한 번
  make_texts.py · check_links.py · show_skills.py · runs.py · sel/   대본 만들기 · 링크 대조 · 부른 스킬 · 코드 복사 대조 · 고르기 물음
tests/                            플러그인 밖 — 사용자에게 가지 않는다
  test_script_link.py             공유 벡터 대조 · 명령 줄
  test_reading_time.py            속도가 근거 문서의 표와 같은지 · 세기 · 명령 줄
  test_script_format.py           지시문 찾기가 앱 시험의 경우와 같은지 · 잘못 쓴 괄호 · 명령 줄
  test_no_network.py              바깥 요청 0
  test_directory_rules.py         플러그인 폴더가 디렉터리의 파일 규칙(비 Verified 조직)을 지키는지
  test_skill_commands.py          SKILL.md 의 명령을 그대로 bash · zsh(noclobber 포함)로 · 핵심 값을 틀리게 옮기면 멈추는지
  skill_code.py                   SKILL.md 의 python 블록을 파일로 적어 시험 · e2e 가 불러 쓴다
  vectors/link-vectors-v1.json    공유 벡터 사본
docs/                             플러그인 밖
  reading-pace-studies-20261104.md    읽는 시간 속도의 근거(측정한 네 언어의 숫자 · 연구 둘 · 정한 규칙)
  coupe-recount-20261104.py           Coupé 2019 데이터를 우리 셈법으로 다시 세는 코드
  skill-e2e-20261108.md               끝에서 끝 시험 결과(링크 상한 · 스킬 고르기)
  skill-e2e-20261109.md               코드를 SKILL.md 로 옮긴 뒤 끝에서 끝 시험(코드 옮겨 적기)
```

- 플러그인을 하위 폴더에 둔다. 시험 · 벡터 · 이 문서가 사용자에게 가지 않게 한다. 디렉터리 검증은 플러그인 폴더만 센다
  (77e4297 검증 «18 files» = 파일 10 + 폴더 8).
- 스킬은 셋으로 나눈다(대본 다듬기 · 읽는 시간 · 링크). Claude 는 `description` 만 읽고 스킬을 고른다. 한 가지 일만 하는
  스킬이 고르기 쉽다(`skills/how-to` «Keep it focused»).
- 스킬 글(`SKILL.md`)과 목록 설명은 영어로 쓴다. Claude 는 사용자의 언어로 답한다.
- 목록 글은 무료판 문턱을 중립 문장 하나로 알린다(11-08 제품 판단). 앱은 링크로 받은 대본을 길이와 상관없이 넣고,
  무료판은 300 자까지의 대본만 «읽기 시작»할 수 있다(iOS `FreeTier.characterLimit` · Android `CHARACTER_LIMIT`). 가격 · 권유 · 결제 링크는 넣지 않는다.
- 측정 방법(어디서 누구의 말을 어떻게 받아 적었는지)은 공개 판에 넣지 않는다(11-08 제품 판단). 측정한 숫자만 연구 문서에 둔다.
- 마켓플레이스 파일(`marketplace.json`)은 두지 않는다. 로컬 시험은 `--plugin-dir` · zip 올리기로 하고, 배포는 디렉터리로 한다.
  그래서 `claude plugin validate` 의 권고 «README 에 마켓플레이스 설치 줄이 없다»는 따르지 않는다. 디렉터리 판은 claude.ai 에서
  더하고, 문서에 그 판의 `/plugin install` 줄이 없다(code.claude.com `plugins/publish` · claude.com `plugins/submit` · 11-08 읽음).
- 아이콘은 `plugin.json` 의 `icon` 칸으로 싣는다. 디렉터리는 목록에 그 칸을 읽고, 기본 위치는 없다(`plugins/manifest-reference`).
  claude.ai 에 zip 으로 올린 판은 이 칸이 있어도 기본 아이콘을 보였다(11-08). 디렉터리 목록에서 어떤지는 확인하지 못했다.

## 코드 자리

디렉터리가 v0.1.0(4e9e655)을 거절했다(11-09 · «Files outside the allowed types accepted only from Verified organizations»).
Verified 가 아닌 조직은 Markdown · text · JSON · YAML · PNG · JPEG · GIF · WebP · ICO 만 낼 수 있다. 이름이 무엇이든 그 밖의 파일 ·
`#!` 로 시작하는 파일 · 패키지 관리자 설정은 안 된다. 텍스트는 NUL 없는 UTF-8 이다(포털 문구 · 11-05 무렵 생긴 규칙 · 문서에는 없다).
Verified 를 청하는 길은 없다(anthropics/claude-plugins-official#7024). 그래서 플러그인에 코드 파일을 두지 않는다.

- 스킬마다 코드는 `SKILL.md` 의 마지막 절 «The code» 의 python 블록 하나에 둔다. 머리 · 단계 글이 앞에 있어 내용으로 종류를
  가리는 도구가 Markdown 으로 읽는다(Magika 1.1 셋 다 Markdown · `file` 은 Python 으로 읽는다 · Anthropic `skills/pdf/SKILL.md` 도 같다).
- Claude 는 블록을 `mktemp` 임시 파일에 적고 대본을 표준 입력으로 넘겨 실행한 뒤 지운다(명령 한 줄 · heredoc 둘 · bash · zsh 확인).
  실행마다 새로 적는다. 옛 파일을 다시 쓰면 낡은 코드가 돈다.
- 코드는 핵심 값을 옮겨 적다 틀리면 스스로 멈춘다(«the code was not copied exactly»). 링크는 링크 머리 · base64url 글자
  (`-` `_` · `=` 빼기) · 되읽기를, 읽는 시간은 속도 숫자 32 개에 자리 번호를 곱한 합(`PACE_CHECK` · 두 숫자를 바꿔 적어도 잡는다)을,
  검사는 전각 괄호 접기를 본다. 함수 몸을 틀리게 옮긴 것은 못 잡는다. 그것은 e2e 가 SKILL.md 와 글자까지 견준다.
  링크는 고정 링크와 견주지 않는다. zlib-ng 같은 다른 zlib 은 다른 바이트를 내고, 앱은 그것도 읽는다.
- 명령은 `cat >|` 로 적어 noclobber 셸에서도 돌고, `s=$?; rm -f "$f"; (exit $s)` 로 코드의 종료 상태를 남긴다.
- 시험은 `tests/skill_code.py` 로 블록을 뽑아 예전 파일과 같은 모듈 이름으로 부른다. `test_directory_rules.py` 가 파일 규칙을 지킨다.
- `plugin.json` 의 `icon` · `supportUrl` · `privacyPolicyUrl` 은 포털이 경고해도 둔다. 디렉터리가 목록에 읽는 칸이다
  (code.claude.com `plugins/manifest-reference` «Anthropic's directory reads the `icon`, …, `supportUrl`, `privacyPolicyUrl` … fields»).

## 링크 꼴

링크 꼴 v1 은 VoiceScroll 앱과 웹이 함께 지키는 공개 계약이다. 여기서 바꾸지 않는다. 아래 «명세»는 그 계약의 앱 쪽 문서다.

```
https://www.voice-scroll.com/s#v1.<base64url(zlib(UTF-8 대본))>
```

- 쓰는 쪽은 명세의 Python 참조 그대로다: zlib 9 단계 · base64url · `=` 없음 · 나중 칸 없음.
- 링크 코드는 받은 글 그대로 담는다. 줄바꿈 정리 · 앞뒤 빈 줄 빼기는 읽는 쪽(앱 · `/s`)이 한다.
- 스킬 글은 Claude 가 마크다운 기호 없이 글만 넘기게 한다(명세 «Claude 스킬은 마크다운을 쓰지 않는다»). 기호를 뺐으면 사용자에게 말한다.
- 스킬은 대본을 표준 입력으로 넘긴다. Claude Code 에서 사용자 프로젝트에 파일을 남기지 않는다.
- 1 MiB 를 넘는 대본 · 빈 대본 · UTF-8 이 아닌 파일은 링크를 만들지 않는다(앱이 `tooLarge` · `empty` · `brokenLink` 로 받는다).
- 링크는 10,000 자까지 만든다(`COPY_LIMIT`). Claude 는 코드가 낸 링크를 답에 다시 옮겨 적는다. 끝에서 끝 시험에서 10,800 자
  이하 22 회는 모두 글자까지 같았고, 13,310 자 1 회가 글자 하나를 틀렸다(`docs/skill-e2e-20261108.md`). 10,000 자 링크는 대본으로 fr 14 · es · de 16 · pt-BR 20 ·
  en 22 · ko · ja 26 · zh 29 ~ 30 분이다(블로그 번역 본문을 읽는 시간 스킬로 잼 · 11-08). 목록 글은 «약 15 ~ 30 분»으로 쓴다.
- 넘으면 코드가 대본을 나눠 부분마다 링크를 한 줄씩 낸다. 빈 줄(단락) 경계에서 나누고, 혼자 넘는 단락은 줄 경계에서 나눈다.
  앞 부분부터 상한까지 채운다. 부분 수를 전체 링크 길이로 셈하지 않는다. 부분마다 따로 압축하면 앞 부분의 압축 맥락을 잃어
  부분 링크의 합이 전체 링크보다 길다. 그래서 부분마다 링크 길이를 재며 채운다. 한 줄이 혼자 넘으면 오류를 내고, 스킬 글이 Claude 에게
  문장 끝에 줄바꿈을 넣어 다시 실행하게 한다. Claude 가 나누면 파일로 받은 대본도 다시 써야 하므로 나누기는 코드가 한다(리뷰 11-08).
- 대본이 이미 글 파일이면 스킬 글이 Claude 에게 경로를 넘기게 한다. Claude 가 대본을 다시 쓰다 낱말을 바꾼 일이 28 회 중 1 회 있었다.

## 대본 다듬기

`script-format` 스킬은 대본을 앱이 그대로 읽는 꼴로 쓴다. 말하는 글은 그대로 두고, 말하지 않는 글을 지시문 괄호에 넣고,
스킬 끝의 검사 코드로 괄호를 앱과 같은 규칙으로 검사한다. 앱 사실은 iOS v2.0.21-b109 · Android v2.0.11-vc94 태그에서 읽었다.

- 설명(`description`)은 VoiceScroll 이나 프롬프터에서 읽는다고 한 대본, 또는 `[pause]` 같은 지시문을 청한 경우에만 불리게 쓴다.
  그냥 «발표 대본 써 줘»에 불리면 답이 청하지 않은 VoiceScroll 을 권한다(디렉터리 «홍보 수단» 정책 · `docs/skill-e2e-20261108.md`).
- `script-format` · `script-link` 설명에 «VoiceScroll 이나 프롬프터를 청하지 않았으면 VoiceScroll 을 꺼내지 않는다»를 넣었다.
  넣기 전에는 스킬이 안 불린 일반 대본 답 6 회 중 5 회가 끝에 VoiceScroll 을 권하는 한 줄을 붙였다(11-08 제품 판단 «줄인다»).

- 괄호 안은 «읽지 않는 말»이 아니라 «기다리지 않는 말»이다(`CueMarkerRule`). 앱이 드는 세 쓰임: 말하지 않는 지시문 ·
  인식이 틀리는 고유 이름(소리 내어 읽는다) · 테이크마다 바뀌는 빈칸(소리 내어 읽는다).
- 읽는 화면은 지시문을 줄에서 빼고, 바로 앞 낱말에 닿을 때 읽는 상자 바로 아래에 띄운다(자리가 모자라면 다른 자리 · iOS · Android `CueCaptionPlacement`). 앱이 만드는 자막에서도 빠진다.
  그래서 스킬은 고유 이름을 사용자가 청할 때만 괄호에 넣는다. 넣으면 이름이 줄에서 빠지고 자막에도 없다고 말하게 한다.
- 기호는 사용자가 고른다: 기본 `[ ]`(켜짐) · `( )` · `{ }` · 끄기. 앱 설정 이름은 «Script Directions»(ko «대본 지시문»)다.
  코드는 `--marks` 로 셋을 받는다. 앱 설정의 임의 두 글자는 Android 가 받지 않아 셋만 둔다.
  끄기는 규칙이 `nil` 이라 앱이 괄호 안 낱말도 기다린다(iOS `ScriptItem` · Android `settings_cue_markers_off`). 사용자가 껐다고 하면
  스킬 글이 말하지 않는 글을 빼고 설정을 다시 켜면 지시문을 둘 수 있다고 말하게 한다(리뷰 11-08).
- 전각 `［］【】〔〕` 은 `[ ]`, `（）` 는 `( )`, `｛｝` 는 `{ }` 로 접힌다. 깊이를 세어 겹친 괄호는 바깥 하나가 된다.
- ⚠️ 닫히지 않은 여는 괄호는 그것만 글로 남는 것이 아니다. 깊이가 0 으로 돌아오지 않으니 **그 뒤의 지시문이 모두 무시된다**
  (앱 코드의 결과 · 앱 시험은 닫히지 않은 괄호 하나만 본다). 코드가 이것을 문제로 알린다.
- 코드가 알리는 문제: 닫히지 않은 여는 괄호 · 아무것도 닫지 않는 닫는 괄호 · 여러 줄에 걸친 지시문(그 줄들을 앱이 기다리지 않는다) ·
  괄호 안 괄호. 지시문 목록도 내어 Claude 가 뜻하지 않은 지시문을 보게 한다.
- 마크다운은 쓰지 않는다. 앱은 링크로 받은 글이 마크다운 꼴이면 기호를 빼고 제목을 `[제목]` 지시문으로 바꾸지만(`looksLikeMarkdown`),
  웹 `/s` 는 글 그대로 보인다. 스킬은 제목을 처음부터 `[제목]` 줄로 쓴다.

## 읽는 시간

스킬 끝의 세기 코드(`--lang <언어> -`)가 대본을 세어 시간 범위를 낸다. `--seconds <초>` 는 그 시간에 맞는 길이를 낸다.
Claude 는 낱말을 직접 세지 않고 코드를 실행한다(스킬 글이 시킨다).

- 단위: ko · ja · zh · th 는 글자, 나머지는 낱말이다. 글자는 유니코드 글자 · 숫자 · 결합 부호만 센다(공백 · 문장부호 · 마크다운 기호는 빠진다).
  낱말은 공백으로 가른 덩이 중 글자나 숫자가 든 것이다. 측정이 센 법과 같다.
- `[ ]` 안도 센다. 앱에서 괄호는 «기다리지 않는 말»이고, 고유 이름 · 빈칸은 소리 내어 읽는다(`CueMarkerRule`).
- 속도는 넷으로 나뉜다. 근거와 셈은 `docs/reading-pace-studies-20261104.md` 다.

| 무리 | 언어 | 근거 |
|---|---|---|
| 측정 | ko · en · cs · zh | VoiceScroll 이 영상 속 사람 말로 잰 p25 · 중앙값 · p75(숫자만 연구 문서에 둔다 · 측정 방법은 공개하지 않는다) |
| 연구 | ca · de · es · fi · fr · hu · it · ja · sr · th · tr · vi · ar · he · nb · nl · pl · pt · ru · sv | Coupé 2019 재계산 · IReST 를 보통 빠르기로 낮춘 값. 범위 폭은 측정 언어의 퍼짐 |
| 가까운 언어 | sk · hr · bs · uk · da · no · nn | cs · sr · ru · nb 의 값 |
| 없음 | ro · el · hi · id · ms | 자료를 찾지 못했다. 코드가 «no reading pace» 로 멈춘다 |

- 측정 밖의 언어는 출력의 `pace source:` 가 `rough` 로 시작한다. 스킬 글이 Claude 에게 «어림»이라고 말하게 한다.
- 시험이 근거 문서의 표를 읽어 코드의 값과 대조한다. 표나 값 한쪽만 고치면 시험이 실패한다.
- 앱은 언어마다 고정 속도를 두지 않는다(`FallbackPacer` «an absolute WPM cannot be shared across languages»). 이 스킬의 속도는
  앱이 화면을 넘기는 속도와 상관이 없다. 대본을 쓰는 사람에게 길이를 어림해 주는 값이다.

## 판정 기준

| 요구한 것 | 이 저장소가 재는 법 |
|---|---|
| 스킬이 만든 링크가 공유 벡터 34 개와 같다 | 34 개를 모두 가른다. 쓰는 쪽이 만들 수 있는 벡터 8 개(`www` · `/s` · `v1` · zlib 9 · `=` 없음 · 나중 칸 없음)는 글자 하나까지 같다. 나머지 26 개는 읽는 쪽만 보는 경우다(실패 · zlib 1 단계 · `=` · 맨 도메인 · `/s/` · 나중 칸). 시험에 벡터마다 까닭을 적었다. 벡터 파일이 바뀌면 sha256 시험이 먼저 실패한다 |
| 스킬 실행에 바깥 요청이 0 이다 | 코드가 들이는 모듈은 `argparse` · `base64` · `re` · `statistics` · `sys` · `unicodedata` · `zlib` 뿐이다(AST 검사). 플러그인 파일이 적은 호스트는 voice-scroll.com 뿐이다. macOS 에서 `sandbox-exec` 로 네트워크를 막고 실행해도 결과가 같다 |
| 설치 수를 읽을 수 있다 | 디렉터리에 실린 뒤 개발자 포털(claude.ai/directory/manage)의 **Usage** 탭이 설치 · 판 · 스킬별 실행 수 · 오류율을 보인다(`directory/publish` «Usage figures»). 실리기 전에는 읽을 길이 없다 |

- ⚠️ 글자 하나까지 같다는 것은 zlib 1.2 대 라이브러리에서 본 것이다. claude.ai 샌드박스의 zlib 이 다른 구현(zlib-ng 등)이면
  링크 글자가 달라질 수 있다. 읽는 쪽은 어느 zlib 출력이든 같게 읽는다(명세 «압축 단계는 아무것이나 된다»).

## 시험

```bash
python3 -I -m unittest discover -s tests          # 벡터 · 명령 줄 · 바깥 요청 0
claude plugin validate ./voicescroll               # 매니페스트 · 스킬 머리
claude --plugin-dir ./voicescroll                  # Claude Code 에서 스킬을 불러 써 본다
mkdir -p dist && (cd voicescroll && zip -r ../dist/voicescroll.zip . -x '*.DS_Store' -x '*__pycache__*')  # claude.ai 올리기용
```

끝에서 끝 시험은 Claude 를 실행하므로 돈이 든다(링크 14k 자 한 번에 약 $0.4). 실행 폴더는 `$TMPDIR/voicescroll-e2e` 다.

```bash
python3 -I e2e/make_texts.py <사이트 소스> /tmp/vs-prompts                        # 블로그 본문으로 길이별 링크 요청을 만든다
e2e/run.sh link-ko-9000 sonnet /tmp/vs-prompts/link-ko-9000.txt                    # 한 번 실행
python3 -I e2e/check_links.py "$TMPDIR"/voicescroll-e2e/link-*                     # 답의 링크 = 코드 출력인지
for f in e2e/sel/*.txt; do e2e/run.sh "sel-$(basename "$f" .txt)" sonnet "$f"; done
python3 -I e2e/show_skills.py "$TMPDIR"/voicescroll-e2e/sel-*                      # 물음마다 부른 스킬
```

## 멈출 자리

다음 셋은 하기 전에 멈추고 제품 결정을 받는다. 셋 다 밖으로 나가는 일이다.

1. ✅ claude.ai 계정에 올려 시험하기(11-08 · VoiceScroll 의 Team 작업 공간 · 6b55336). 스킬 셋이 claude.ai 코드 샌드박스에서 돌았고
   링크 · 읽는 시간 · 검사 결과가 이 저장소 코드 출력과 같았다. 올린 판은 올린 계정에만 보인다(같은 조직의 다른 계정에 없음).
   남에게 보이는 길은 «조직에 게시» · «공유» 둘이다. 결과 정본은 `docs/skill-e2e-20261108.md` «claude.ai».
2. 저장소를 공개로 바꾸기. 제출 · 검증은 private 로 해도 되고(포털이 소스를 Anthropic 에 올려 검사한다), 게시 전에는 공개여야 한다.
   11-08 이력 점검 뒤 파일의 로컬 경로 · 내부 이름 · 비공개 저장소 이름을 고쳤다(VS-ID 는 남긴다 · 열 수 없는 이슈 번호다).
   커밋 작성자 메일 · 커밋 메시지에는 아직 남아 있다. 공개 직전에 이력을 새 커밋 하나로 만든다(작성자 GitHub noreply).
   지난 이력은 private 사본에 남긴다.
3. 디렉터리에 내기 — 링크 받기가 든 앱 판이 출시된 뒤. 유료 claude.ai 계정이 낸다(Team 이면 Owner 나 Directory 권한).
   목록의 이름 · 설명은 `plugin.json` 과 README 에서 읽고, 고치려면 새 판을 낸다.

근거: claude.com `plugins/submit` · `plugins/pre-submission-checklist` · `directory/publish` · code.claude.com `plugins/manifest-reference`(11-08 읽음).

## 범위 밖

- 대본을 서버 · 로그 · 분석으로 보내지 않는다. 스킬은 바깥 주소를 부르지 않는다.
- 링크 꼴 v1 을 바꾸지 않는다.
- 가격 숫자 · «구독 없음»을 쓰지 않는다. 플랫폼은 출시한 것만 쓰고, Mac 은 조건과 함께 쓴다. 온디바이스 절대 문장은 «기본값은» 틀로 쓴다.
- OpenAI · Anthropic 과 제휴가 있다고 쓰지 않는다.
- 결제 링크 · 업그레이드 권유를 넣지 않는다(디렉터리 정책 «주로 광고나 홍보의 수단인» 소프트웨어).

## 남은 일

1. ✅ 꼴 · 링크 스킬 · 벡터 시험 · 바깥 요청 0 시험
2. ✅ 읽는 시간 스킬: 측정 네 언어 · 연구 스무 언어 · 가까운 언어 일곱 · 앱 언어 다섯은 어림하지 않음(위 «읽는 시간»)
3. ✅ 대본 다듬기 스킬: 앱의 지시문 규칙과 같은 검사 코드(위 «대본 다듬기»)
4. ✅ Claude Code 끝에서 끝 시험: 링크 상한 10,000 자와 넘을 때 나누기 · 파일은 경로로 · `script-format` 이 VoiceScroll 이나
   프롬프터를 말하지 않은 대본에 불리지 않게 설명을 좁혔다(`docs/skill-e2e-20261108.md`)
5. ✅ `claude plugin validate` · 리뷰(3a8d4af.. 전체 · 링크 나누기를 코드로 옮김 · 지시문 끄기) · 알림
