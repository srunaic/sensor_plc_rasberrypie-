# Gas Safety PLC Monitoring System (가스 설비 안전 모니터링 시스템) 🛡️

현장 가스 설비의 안전을 실시간으로 감시하고, 위험 상황 시 자동 차단(Interlock) 및 이력을 관리하는 통합 모니터링 시스템입니다.

---

## 🚀 Key Features (주요 기능)

### 1. Gas Safety Simulation (가스 안전 시뮬레이션)
- **Realistic Data Generation**: 5 PPM 내외의 안정적인 평상시 상태와 1% 확률로 발생하는 가스 누출(Leak) 시나리오 시뮬레이션.
- **Auto-Interlock Logic**: 가스 농도가 40 PPM을 초과하면 **Interlock Valve 즉시 차단** (Status: FAULT).
- **Recovery Cycle**: 가스 안정화 후 15초(현장 리셋 가정) 뒤 자동으로 **NORMAL** 상태 복구 프로세스.

### 2. Edge & Backend Architecture
- **Edge Collector**: 라즈베리파이 역할을 하며 Modbus-TCP로 PLC 데이터를 폴링하고 서버로 전송.
- **Real-time Synchronization**: WebSockets 기반 실시간 데이터 브로드캐스팅.
- **Unified Server**: FastAPI가 백엔드 API와 정적 프론트엔드 파일을 동시에 서빙하는 최적화된 구조.

### 3. Safety-First Web UI
- **Emergency Banner**: 알람 발생 시 상단에 고정되는 붉은색 경고 사이렌 배너.
- **State-First UX**: 수치보다 상태(NORMAL/ALARM)를 명확하게 시각화.
- **No-Control Policy**: 보안을 위해 제어 기능을 배제한 읽기 전용 모니터링 대시보드.

---

## 🛡️ Technical Resolution Log (문제 해결 이력)

1. **CORS & Dynamic Host**: 다양한 환경(localhost, IP 등)에서 통신 거부 문제를 `window.location.host` 동적 감지 로직으로 해결.
2. **Schema Integrity**: 가스 데이터 필드 추가에 따른 DB 충돌을 스키마 초기화 로직 보강으로 해결.
3. **Frontend Stability**: 데이터 수집 전 `null` 값에 의한 `toFixed` 런타임 에러를 Optional Chaining으로 방어.
4. **Deployment Optimization**: Cloudflare Build 경로 충돌 이슈를 Unified Architecture(단일 서버 통합) 전환으로 극복.

---

## 🌐 External Access (외부 접속 가이드)

### 1. Static Layout (UI 확인용)
👉 [https://sensor-plc-rasberrypie.pages.dev/](https://sensor-plc-rasberrypie.pages.dev/)

### 2. Live Tunnel (실시간 데이터 연동용)
외부 PC에서 현재 로컬의 실시간 데이터를 확인하려면 **Cloudflare Tunnel** 사용을 추천합니다:
```bash
cloudflared tunnel --url http://localhost:8000
```
생성된 `https://*.trycloudflare.com` 주소를 통해 전 세계 어디서나 접속 가능합니다.

---

## ✅ Final Verification Result
- [x] 가스 알람 발생 시 즉각적인 밸브 차단 확인
- [x] 안정화 후 15초 카운트다운 및 자동 복구 확인
- [x] 모든 이벤트의 SQLite DB 영구 기록 성공
- [x] 단일 포트(8000) 통합 서비스 안정성 검증 완료
