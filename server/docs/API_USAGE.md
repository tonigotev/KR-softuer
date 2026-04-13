# API Usage

Base path: `/v1`

Authentication: JWT Bearer token in `Authorization` header.

## Public Endpoints

### Register Doctor

- `POST /auth/register/doctor/`
- Body:
```json
{
  "email": "doctor@example.com",
  "full_name": "Dr. Ivan Ivanov",
  "password": "StrongPass123",
  "password2": "StrongPass123",
  "physical_address": "Sofia, 1 Main St",
  "weekly_schedule": [
    {"weekday": 0, "start_time": "08:30:00", "end_time": "12:00:00"},
    {"weekday": 0, "start_time": "13:00:00", "end_time": "18:30:00"}
  ]
}
```
- Success: `201 Created` + access/refresh token.

### Register Patient

- `POST /auth/register/patient/`
- Body:
```json
{
  "email": "patient@example.com",
  "full_name": "Petar Petrov",
  "password": "StrongPass123",
  "password2": "StrongPass123",
  "phone_number": "0888123456",
  "primary_doctor_id": 1
}
```
- Success: `201 Created` + access/refresh token.

### Login

- `POST /auth/login/`
- Body:
```json
{"email": "doctor@example.com", "password": "StrongPass123"}
```
- Success: `200 OK` + access/refresh token.

## Protected Endpoints

### Update Weekly Working Schedule (Doctor)

- `PUT /scheduling/doctors/me/weekly-schedule/`
- Body:
```json
{
  "slots": [
    {"weekday": 1, "start_time": "09:00:00", "end_time": "17:00:00"}
  ]
}
```

### Add Temporary Working Schedule Change (Doctor)

- `POST /scheduling/doctors/me/temporary-schedule/`
- Body:
```json
{
  "start_datetime": "2026-04-20T08:00:00+03:00",
  "end_datetime": "2026-04-25T18:00:00+03:00",
  "slots": [{"weekday": 0, "start_time": "10:00:00", "end_time": "14:00:00"}]
}
```

### Add Permanent Working Schedule Change (Doctor)

- `POST /scheduling/doctors/me/permanent-schedule/`
- Rule: `effective_from` must be at least 7 days in the future.

### Create Visit (Patient)

- `POST /scheduling/visits/`
- Body:
```json
{
  "starts_at": "2026-04-28T09:00:00+03:00",
  "ends_at": "2026-04-28T09:20:00+03:00"
}
```

Business rules enforced:
- patient can only book with their personal doctor,
- visit must be inside doctor working time,
- visit must be created at least 24h in advance,
- no overlap with existing scheduled visits.

### Cancel Visit

- `POST /scheduling/visits/{visit_id}/cancel/`
- Allowed only for doctor or patient in that visit.
- Must be at least 12h before visit start.

### My Visits

- `GET /scheduling/visits/me/`
- Optional query params:
  - `status=scheduled|cancelled`
  - `from=YYYY-MM-DD`

## Error Handling

Common status codes:
- `400` validation/business rule failure
- `401` missing/invalid token
- `403` role/permission denied
- `404` resource not found
