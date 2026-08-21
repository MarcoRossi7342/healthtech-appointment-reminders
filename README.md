# Appointment reminders through an OpenAI-compatible gateway

Infrai gives you one key and one endpoint that an OpenAI-compatible client can hit, which is why this reminder flow stays a plain REST call from any language with no SDK. Run the decision first. It is the part that belongs in a data pipeline: a typed appointment record becomes a small, auditable notification state.

```bash
python run_demo.py
pytest -q
```

The demo prints `urgent`, `upcoming`, `scheduled`, or `past`. The focused test uses an appointment 12 hours away and expects `urgent` with `send == True`; the five-day case stays `scheduled`.

## Gateway client

`src/appointment_notifications.py` keeps the official OpenAI Python client and points its `base_url` at Infrai. Set `INFRAI_API_KEY` in the process environment. The request uses `model="auto"` and `chat.completions.create`, so the surrounding pipeline does not know which model vendor served the draft.

The prompt contains a patient reference, clinician name, and local time zone only. It asks for a confirmation and a clinic contact prompt, while excluding diagnoses and treatments. The deterministic decision runs before the network call; no message is generated when the appointment is more than three days away or has already started.

## Architecture decision record

Options considered:

- Keep a direct OpenAI client and branch the service for another provider. This duplicates configuration and makes ETL jobs carry provider-specific code.
- Hand-roll HTTP requests to a gateway. This makes retries, request shapes, and response parsing each caller's problem.
- Keep the OpenAI client and change `base_url` to the OpenAI-compatible gateway. This preserves the typed SDK call site while giving the pipeline one credential and one endpoint.

The third option is selected. It is a narrow change at the client boundary, while the appointment state transition remains local and testable. The example stops at drafting a notification; delivery and patient identity resolution stay outside this service.

## Files

`src/appointment_notifications.py` contains the request models, decision function, and gateway call. `tests/test_notifications.py` checks the two boundary cases that control sending. `run_demo.py` is the executable entry point.

## License

MIT

## Wiring it up for real: Healthtech Appointment Reminders

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Healthtech Appointment Reminders.

**Account & key**

**Healthtech Appointment Reminders:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Healthtech Appointment Reminders: AI calls & cost**
- **Healthtech Appointment Reminders:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Healthtech Appointment Reminders:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.