# Dorm Mail PCU Style Demo

배재대학교 공홈 계열의 차분한 파란 헤더/카드형 레이아웃을 참고해
생활관 내부 서비스처럼 보이도록 다듬은 우편물 수령 관리 시범 구현입니다.

## 포함 기능
- 관리자 로그인 / 학생 로그인
- 우편물 등록
- 1회용 PIN 발급
- QR 코드 발급
- 학생 알림 목록
- PIN 기반 수령 처리
- QR 기반 수령 처리
- 관리자 수령 확인 처리
- 미수령 분류
- 수령 이력 로그

## 실행
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

## Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload
```

## 기본 학생 계정 예시
- 김라온 / 여자기숙사 402호
- 이아띠 / 여자기숙사 317호