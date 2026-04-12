# Zippy – UC03: Odoslanie balíka

## Setup

```bash
pip install kivy
```

## Run

```bash
cd zippy
python main.py
```

## Project structure

```
zippy/
├── main.py                     # App entry point
├── theme.py                    # Design tokens, reusable widgets
├── requirements.txt
├── models/
│   └── order.py                # Order, PackageDetails, Address dataclasses
├── services/
│   ├── socket_service.py       # WebSocket stub (ready for real impl)
│   └── order_service.py        # Business logic + mock data
└── screens/
    ├── base_screen.py          # Shared shell (header, nav, FAB)
    ├── home.py                 # Home screen
    ├── step1_package.py        # Step 1 – Package details
    ├── step2_addresses.py      # Step 2 – Sender & recipient
    ├── step3_payment.py        # Step 3 – Payment (incl. error state)
    └── step4_confirm.py        # Step 4 – Confirmation
```

## Simulating a payment failure

In `screens/step3_payment.py`, change:

```python
success = self.app.shipment_service.submit_order(simulate_failure=False)
```
to:

```python
success = self.app.shipment_service.submit_order(simulate_failure=True)
```

## Socket integration

When your backend is ready, open `services/socket_service.py` and replace
the stub bodies of `connect()`, `disconnect()`, and `emit()` with real
`websockets` or `python-socketio` calls. All event subscriptions and
order submission calls are already wired up throughout the screens.
