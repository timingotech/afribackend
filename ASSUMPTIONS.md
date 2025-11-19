ASSUMPTIONS for backend implementation

- The frontend (mobile) handles map rendering and routing; backend stores coordinates and calculates estimates using a third-party service during integration (not included in scaffold).
- OTP is implemented as a simple model that stores codes; in production this should be sent over SMS via a gateway and TTL/attempt tracking should be stricter.
- Payments are modeled but no gateway integration is included. The scaffold stores `PaymentMethod` tokens as placeholders for later integration.
- WebSockets / realtime tracking are optional. The scaffold supports polling; for realtime recommend adding Django Channels or external socket server.
- Admin actions use default Django admin only.
- Rate-limiting and throttles should be added (e.g., DRF throttling, Redis-based limits). Not implemented in this initial scaffold but hooks are in settings.
- Tests included are minimal; the project needs expanded unit/integration tests before productiion.
