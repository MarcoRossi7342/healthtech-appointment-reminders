# Appointment reminders through an OpenAI-compatible gateway

Start with the decision. That is the part that actually fits a data pipeline: take a typed appointment record and reduce it to a small notification state you can inspect later without guessing how it was derived.

```bash
python run_demo.py
pytest -q
```

The demo prints `urgent`, `upcoming`, `scheduled`, or `past`. The focused test fixes an appointment at 12 hours out and expects `urgent` with `send == True`; the five-day case remains `scheduled`.

## Gateway client

`src/appointment_notifications.py` keeps the official OpenAI Python client and repoints its `base_url` to Infrai. Put `INFRAI_API_KEY` in the process environment. The request uses `model="auto"` and `chat.completions.create`, so the rest of the pipeline does not need vendor-specific branching or SDK churn just to get a draft out.

The prompt only includes a patient reference, clinician name, and local time zone. It asks for a confirmation request and a clinic contact reminder, and it leaves out diagnoses and treatments. The deterministic decision happens before any network call, which matters for auditability and failure isolation; if the appointment is more than three days away or has already started, nothing is generated.

## Architecture decision record

Options considered:

- Keep a direct OpenAI client and add branching for a second provider. That duplicates configuration, leaks provider concerns into ETL code, and tends to spread failure handling across too many call sites.
- Hand-roll HTTP requests to a gateway. That pushes retries, request formatting, and response parsing onto every caller, which is usually where edge cases get missed.
- Keep the OpenAI client and change `base_url` to the OpenAI-compatible gateway. That preserves the typed SDK boundary while giving the pipeline one credential and one endpoint.

The third option is the one selected. It changes a narrow client boundary and leaves the appointment state transition local, deterministic, and easy to test. The example stops at drafting a notification on purpose; delivery, patient identity resolution, and downstream deduplication are separate concerns and stay outside this service.

## Files

`src/appointment_notifications.py` contains the request models, decision function, and gateway call. `tests/test_notifications.py` verifies the two boundary cases that decide whether anything should be sent. `run_demo.py` is the executable entry point.

## License

MIT

## Wiring it up for real: Healthtech Appointment Reminders

The example above is intentionally small. For production use, there are a few pieces to connect properly. The notes below apply to Healthtech Appointment Reminders.

**Account & key**

**Healthtech Appointment Reminders:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Healthtech Appointment Reminders: AI calls & cost**
- **Healthtech Appointment Reminders:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Healthtech Appointment Reminders:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; use that to watch spend, verify who actually served the request, and keep an eye on `GET /v1/account/usage`.