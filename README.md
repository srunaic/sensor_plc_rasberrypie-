# 🏭 Gas Facility Safety Monitoring System

> **Live Dashboard:** [https://sensor-plc-rasberrypie.pages.dev/](https://sensor-plc-rasberrypie.pages.dev/) 🚀

이 프로젝트는 산업 현장의 가스 안전을 실시간으로 모니터링하고 가스 누출 시 자동으로 밸브를 차단하는 **클라우드 네이티브 안전 시스템**입니다.

## 🏗️ System Architecture
중간 서버 없이 에지(Edge)와 클라우드 데이터베이스가 직접 통신하는 **Serverless Architecture**를 채택하였습니다.

- **Frontend**: [Cloudflare Pages](https://sensor-plc-rasberrypie.pages.dev/) (React + Vite)
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **Realtime**: Supabase Realtime (Websocket 기반 실시간 업데이트)
- **Edge**: Python Edge Collector (Modbus/TCP 기반 PLC 데이터 수집 및 Supabase REST API 전송)
- **Simulator**: Python PLC Simulator (가스 누출 및 인터락 로직 시뮬레이션)

## ✨ Key Features
- **실시간 모니터링**: 가스 농도, 온도, 압력, 설비 상태를 실시간으로 대시보드에 표시합니다.
- **자동 안전 로직**: 가스 농도 40 PPM 초과 시 시뮬레이터가 즉시 밸브를 차단(Interlock)하고 로그를 남깁니다.
- **안전 감사 이력**: 모든 상태 변화와 경보 알람은 Supabase DB에 영구 기록되어 사후 분석이 가능합니다.
- **Serverless 인프라**: Cloudflare와 Supabase를 활용하여 별도의 서버 유지보수 없이 안정적으로 운영됩니다.

## 🚀 How to Run (Local)

### 1. PLC Simulator 실행
가상 PLC 환경을 구동하여 가스 누출 및 밸브 차단 시나리오를 시뮬레이션합니다.
```bash
python sim/plc_simulator.py
```

### 2. Edge Collector 실행
시뮬레이터로부터 데이터를 읽어 Supabase 클라우드로 직접 전송합니다.
```bash
python edge/collector.py
```

### 3. Web Dashboard 접속
배포된 [도메인](https://sensor-plc-rasberrypie.pages.dev/)에 접속하여 실시간으로 변하는 가스 수치와 이력을 모니터링합니다.

---
*Developed with 🛡️ Safety-First Architecture*
