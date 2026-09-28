# Claude 논문 분석 차단 — 지원팀 문의용 진단

작성일: 2026-09-23 (Asia/Seoul)

## 확인된 상태

- 로컬 앱: Paper2Agent Studio. 웹 서버와 PDF 추출 도구는 동작 중입니다.
- 최근 작업 ID: `950799c6207b`
- 최근 실패 시각: `2026-09-23T10:29:59.601380+09:00`
- 실패 단계: `analyze` (내용 분석). 에이전트 코드 생성 단계에는 도달하지 않았습니다.
- PDF: 서영상_모델페이퍼03.pdf, 21쪽.
- 논문 제목: Quantum-computing-enhanced algorithm unveils potential KRAS inhibitors
- 논문 DOI: https://doi.org/10.1038/s41587-024-02526-3
- 앱 오류: Claude의 안전 정책에 따라 요청이 차단되었습니다. 논문과 요청 내용을 검토하고, 오탐이 의심되면 Anthropic 지원팀에 문의해 주세요.

## 같은 PDF를 사용한 별도 진단 호출에서 확인한 정보

아래 요청 ID는 최근 웹앱 작업 ID와 별개인, 2026-09-23 CLI 재현 호출의 값입니다.

- Claude Code 버전: `2.1.280`
- 모델: `claude-opus-5-5[1m]`
- 차단 분류: `[bio]`
- 공급자 요청 ID: `req_011CfKV9qp49pFqXP6vHYsiD`
- CLI 응답: `type=result`, `subtype=success`, `is_error=true`, `permission_denials=[]`
- 응답의 핵심 문구: `safeguards flagged this session`, `Details: [bio]`
- 동일 설정의 간단한 JSON 연결 진단은 성공했습니다.
- 요청한 작업은 제공된 논문 발췌의 목적·방법·한계 요약, 원문 인용 및 저장소 메타데이터를 JSON으로 반환하는 것입니다. 해당 분석 호출의 파일·셸 도구는 비활성화되어 있었습니다.

이 정보만으로 오탐 여부를 확정할 수는 없습니다. 앱은 차단된 분석을 완료로 표시하지 않았습니다.

## 문의 초안

Hello Anthropic Support,

Please review a possible false positive from Claude Code's biology safeguards. Our local paper-processing application was blocked while requesting a structured summary and source quotations from the published paper "Quantum-computing-enhanced algorithm unveils potential KRAS inhibitors" (DOI: 10.1038/s41587-024-02526-3).

The failing call requested an analysis of supplied excerpts, in Korean, as JSON. File and shell tools were disabled for this call. The application also has a later code-generation stage, but the failure occurred before that stage. A short JSON connectivity request with the same CLI configuration succeeded.

The separately reproduced failure used Claude Code 2.1.280 and claude-opus-5-5[1m]. Its request ID was req_011CfKV9qp49pFqXP6vHYsiD, with the safety category [bio]. The CLI returned subtype=success together with is_error=true and no permission denials.

Could you review whether this is expected and advise on the supported handling of this academic paper-analysis request?

## 공식 지원 경로

- 지원 문의: https://support.claude.com/en/articles/9015913-how-to-get-support
- 모델 안전 검사 안내: https://support.claude.com/en/articles/16049681-why-claude-switched-models-in-your-conversation-with-opus-5-or-opus-5-5

이 파일은 로컬 문의 초안입니다. 지원팀에 전송하거나 논문 원문을 첨부하지 않았습니다.
