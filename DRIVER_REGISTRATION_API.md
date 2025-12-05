# Driver Document Upload API Documentation

## Overview
This API allows drivers to upload required documents for verification and approval. After basic registration and OTP verification, drivers must submit documents including license photos, vehicle photos, and personal information.

**Two Types of Endpoints:**
1. **Regular Driver Endpoints** (`/api/users/driver-profile/`) - For mobile app integration, allows drivers to manage their own profiles
2. **Admin Endpoints** (`/api/users/admin/drivers/`) - For admin panel, allows staff to manage all driver profiles and approve applications

## Base URL
```
https://afribackend-production-e293.up.railway.app
```

## Authentication
All endpoints require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

**Note:** Admin endpoints require users with admin/staff privileges.

## Driver Document Upload Endpoints

### For Mobile App Developers (Regular Driver Endpoints)

#### 1. Create Driver Profile with Documents (Initial Submission)

**Endpoint:** `POST /api/users/driver-profile/create/`

**Description:** Submit driver application for the first time with all required documents.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
# Personal Information
email: driver@example.com
phone: +2349022013174
first_name: John
last_name: Doe
date_of_birth: 1990-05-15
address: 123 Main Street, Lagos Nigeria
city: Lagos
state: Lagos State
zip_code: 100001

# License Information
license_number: ABC123456789
license_expiry: 2025-12-31
license_issued_state: Lagos State
license_front: [FILE] # Front photo of driver's license
license_back: [FILE]  # Back photo of driver's license

# Vehicle Information
vehicle_make: Toyota
vehicle_model: Corolla
vehicle_year: 2020
vehicle_color: Black
vehicle_plate: LAG-123-AB
vehicle_type: Sedan

# Required Photos
profile_photo: [FILE]      # Driver's headshot
vehicle_front: [FILE]      # Front view of vehicle
vehicle_back: [FILE]       # Rear view of vehicle
vehicle_side: [FILE]       # Side view of vehicle
vehicle_interior: [FILE]   # Interior view of vehicle
```

**Response (201 Created):**
```json
{
  "detail": "Driver profile created successfully.",
  "profile": {
    "id": 1,
    "user": {
      "id": 1,
      "email": "driver@example.com",
      "phone": "+2349022013174",
      "first_name": "John",
      "last_name": "Doe",
      "role": "rider",
      "is_active": true,
      "is_staff": false
    },
    "user_id": 1,
    "user_email": "driver@example.com",
    "date_of_birth": "1990-05-15",
    "address": "123 Main Street, Lagos Nigeria",
    "city": "Lagos",
    "state": "Lagos State",
    "zip_code": "100001",
    "license_number": "ABC123456789",
    "license_expiry": "2025-12-31",
    "license_issued_state": "Lagos State",
    "license_front": "https://domain.com/media/licenses/front/license_front_abc123.jpg",
    "license_back": "https://domain.com/media/licenses/back/license_back_abc123.jpg",
    "vehicle_make": "Toyota",
    "vehicle_model": "Corolla",
    "vehicle_year": "2020",
    "vehicle_color": "Black",
    "vehicle_plate": "LAG-123-AB",
    "vehicle_type": "Sedan",
    "profile_photo": "https://domain.com/media/profiles/profile_abc123.jpg",
    "vehicle_front": "https://domain.com/media/vehicles/front/vehicle_front_abc123.jpg",
    "vehicle_back": "https://domain.com/media/vehicles/back/vehicle_back_abc123.jpg",
    "vehicle_side": "https://domain.com/media/vehicles/side/vehicle_side_abc123.jpg",
    "vehicle_interior": "https://domain.com/media/vehicles/interior/vehicle_interior_abc123.jpg",
    "is_approved": false,
    "is_available": false,
    "submitted_at": "2024-11-19T10:30:00Z",
    "disapproval_reason": null,
    "disapproved_at": null
  },
  "email_send_results": {
    "user": "Application confirmation sent to driver@example.com",
    "support": "New application notification sent to support@aafriride.com"
  }
}
```

#### 2. Get/Update Driver Profile (For Existing Profiles)

**Endpoint:** `GET /api/users/driver-profile/`

**Description:** Retrieve the current driver's profile information and document status.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "driver@example.com",
    "phone": "+2349022013174",
    "first_name": "John",
    "last_name": "Doe",
    "role": "rider"
  },
  "date_of_birth": "1990-05-15",
  "address": "123 Main Street, Lagos Nigeria",
  "city": "Lagos",
  "state": "Lagos State",
  "license_number": "ABC123456789",
  "license_expiry": "2025-12-31",
  "is_approved": false,
  "is_available": false,
  "submitted_at": "2024-11-19T10:30:00Z",
  "disapproval_reason": null
}
```

**Endpoint:** `PUT /api/users/driver-profile/`

**Description:** Update driver profile documents and information.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data - include fields to update):**
```
vehicle_color: Blue           # Update vehicle color
license_front: [FILE]         # Replace license front photo
vehicle_interior: [FILE]      # Replace interior photo
address: 456 New Street, Lagos # Update address
```

**Response (200 OK):**
```json
{
  "id": 1,
  "message": "Profile updated successfully",
  "is_approved": false,
  "submitted_at": "2024-11-19T10:30:00Z"
}
```

---

### For Admin Panel (Admin Endpoints)

#### 1. Create Driver Profile with Documents (Admin)

**Endpoint:** `POST /api/users/admin/drivers/`

**Description:** Admin creates driver application with all required documents.

**Headers:**
```
Authorization: Bearer <admin_access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
# Same as regular driver endpoint above
```

**Response (201 Created):**
```json
{
  "detail": "Driver profile created successfully.",
  "profile": {
    "id": 1,
    "user": {
      "id": 1,
      "email": "driver@example.com",
      "phone": "+2349022013174",
      "first_name": "John",
      "last_name": "Doe",
      "role": "rider"
    },
    "is_approved": false,
    "submitted_at": "2024-11-19T10:30:00Z"
  }
}
```

#### 2. Update Driver Profile/Documents (Admin)

**Endpoint:** `PATCH /api/users/admin/drivers/{driver_id}/`

**Description:** Admin updates specific fields or documents for an existing driver profile.

**Headers:**
```
Authorization: Bearer <admin_access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data - include only fields to update):**
```
vehicle_color: Blue           # Update vehicle color
license_front: [FILE]         # Replace license front photo
vehicle_interior: [FILE]      # Replace interior photo
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": { /* user data */ },
  "vehicle_color": "Blue",
  "license_front": "https://domain.com/media/licenses/front/new_license_front.jpg",
  "vehicle_interior": "https://domain.com/media/vehicles/interior/new_interior.jpg",
  /* ... other fields unchanged ... */
}
```

#### 3. Get Driver Profile (Admin)

**Endpoint:** `GET /api/users/admin/drivers/{driver_id}/`

**Description:** Retrieve complete driver profile with all documents.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "driver@example.com",
    "phone": "+2349022013174",
    "first_name": "John",
    "last_name": "Doe",
    "role": "rider",
    "is_active": true,
    "is_staff": false
  },
  "user_id": 1,
  "user_email": "driver@example.com",
  "date_of_birth": "1990-05-15",
  "address": "123 Main Street, Lagos Nigeria",
  "city": "Lagos",
  "state": "Lagos State",
  "zip_code": "100001",
  "license_number": "ABC123456789",
  "license_expiry": "2025-12-31",
  "license_issued_state": "Lagos State",
  "license_front": "https://domain.com/media/licenses/front/license_front.jpg",
  "license_back": "https://domain.com/media/licenses/back/license_back.jpg",
  "vehicle_make": "Toyota",
  "vehicle_model": "Corolla",
  "vehicle_year": "2020",
  "vehicle_color": "Black",
  "vehicle_plate": "LAG-123-AB",
  "vehicle_type": "Sedan",
  "profile_photo": "https://domain.com/media/profiles/profile.jpg",
  "vehicle_front": "https://domain.com/media/vehicles/front/vehicle_front.jpg",
  "vehicle_back": "https://domain.com/media/vehicles/back/vehicle_back.jpg",
  "vehicle_side": "https://domain.com/media/vehicles/side/vehicle_side.jpg",
  "vehicle_interior": "https://domain.com/media/vehicles/interior/vehicle_interior.jpg",
  "is_approved": false,
  "is_available": false,
  "submitted_at": "2024-11-19T10:30:00Z",
  "disapproval_reason": null,
  "disapproved_at": null
}
```

### 4. List All Driver Profiles

**Endpoint:** `GET /api/users/admin/drivers/`

**Description:** Get list of all driver profiles (admin only).

**Query Parameters:**
- `is_approved` (optional): Filter by approval status (`true` or `false`)

**Examples:**
- `GET /api/users/admin/drivers/` - All drivers
- `GET /api/users/admin/drivers/?is_approved=false` - Pending drivers
- `GET /api/users/admin/drivers/?is_approved=true` - Approved drivers

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user": { /* user data */ },
    "license_front": "https://domain.com/media/licenses/front/license_front.jpg",
    "is_approved": false,
    "submitted_at": "2024-11-19T10:30:00Z",
    /* ... all other fields ... */
  },
  {
    "id": 2,
    "user": { /* user data */ },
    "is_approved": true,
    "submitted_at": "2024-11-18T15:20:00Z",
    /* ... all other fields ... */
  }
]
```

## Required Documents

### Personal Information
- `date_of_birth` (date): Driver's date of birth (YYYY-MM-DD)
- `address` (string): Full residential address
- `city` (string): City of residence
- `state` (string): State/Province
- `zip_code` (string): Postal/ZIP code

### License Documents
- `license_number` (string): Valid driver's license number
- `license_expiry` (date): License expiration date (YYYY-MM-DD)
- `license_issued_state` (string): State/country where license was issued
- `license_front` (file): **REQUIRED** - Front photo of driver's license
- `license_back` (file): **REQUIRED** - Back photo of driver's license

### Vehicle Information
- `vehicle_make` (string): Vehicle manufacturer (e.g., "Toyota")
- `vehicle_model` (string): Vehicle model (e.g., "Corolla")
- `vehicle_year` (string): Vehicle year (e.g., "2020")
- `vehicle_color` (string): Vehicle color
- `vehicle_plate` (string): License plate number
- `vehicle_type` (string): Type (e.g., "Sedan", "SUV", "Hatchback")

### Required Photos
- `profile_photo` (file): **REQUIRED** - Clear headshot of driver
- `vehicle_front` (file): **REQUIRED** - Front view of vehicle showing plate
- `vehicle_back` (file): **REQUIRED** - Rear view of vehicle showing plate
- `vehicle_side` (file): **REQUIRED** - Side profile of vehicle
- `vehicle_interior` (file): **REQUIRED** - Interior view showing cleanliness

## File Upload Requirements

### Supported Formats
- **Images:** JPG, PNG, WEBP
- **Maximum Size:** 5MB per file
- **Minimum Resolution:** 800x600 pixels
- **Quality:** Clear, well-lit, readable text

### Photo Guidelines

#### License Photos
- Must be clear and readable
- All text must be visible
- No glare or shadows
- Full license visible in frame

#### Vehicle Photos
- Good lighting (preferably daylight)
- Vehicle should fill most of the frame
- Clean vehicle for best presentation
- License plate must be clearly visible in front/rear photos

#### Profile Photo
- Professional headshot
- Clear view of face
- Good lighting
- Neutral background preferred

## Approval Process

### Status Fields
- `is_approved` (boolean): Whether driver is approved to drive
- `is_available` (boolean): Whether driver is currently available for rides
- `submitted_at` (datetime): When documents were first submitted
- `disapproval_reason` (string): Reason if application was rejected
- `disapproved_at` (datetime): When application was rejected

### Approval Flow
1. Driver submits documents via API
2. Admin reviews documents in admin panel
3. Admin approves or disapproves with reason
4. Driver receives email notification of decision
5. If approved, driver can start accepting rides

### Admin Actions

#### Approve Driver
**Endpoint:** `POST /api/users/admin/drivers/{driver_id}/approve/`
```json
{
  "detail": "Driver application approved.",
  "email_send_results": {
    "user": "Approval email sent to driver@example.com",
    "support": "Notification sent to support@aafriride.com"
  }
}
```

#### Disapprove Driver
**Endpoint:** `POST /api/users/admin/drivers/{driver_id}/disapprove/`
```json
{
  "reason": "Vehicle does not meet safety standards"
}
```

Response:
```json
{
  "detail": "Driver application disapproved.",
  "email_send_results": {
    "user": "Disapproval email sent to driver@example.com",
    "support": "Notification sent to support@aafriride.com"
  }
}
```

## Error Responses

### 400 Bad Request - Validation Error
```json
{
  "license_front": ["This field is required."],
  "vehicle_plate": ["This field may not be blank."]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 413 Payload Too Large
```json
{
  "detail": "File size exceeds maximum allowed size of 5MB."
}
```

## Complete Example Flow

### Step 1: Register and Verify
```bash
# Register as rider
curl -X POST https://afribackend-production-e293.up.railway.app/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.driver@example.com",
    "phone": "+2349022013174",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "rider",
    "verification_method": "email"
  }'

# Verify OTP
curl -X POST https://afribackend-production-e293.up.railway.app/api/users/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.driver@example.com",
    "code": "123456"
  }'

# Login
curl -X POST https://afribackend-production-e293.up.railway.app/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.driver@example.com",
    "password": "SecurePass123!"
  }'
```

### Step 2: Upload Documents
```bash
curl -X POST https://afribackend-production-e293.up.railway.app/api/users/admin/drivers/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "email=john.driver@example.com" \
  -F "phone=+2349022013174" \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "date_of_birth=1990-05-15" \
  -F "address=123 Main Street, Lagos Nigeria" \
  -F "city=Lagos" \
  -F "state=Lagos State" \
  -F "zip_code=100001" \
  -F "license_number=ABC123456789" \
  -F "license_expiry=2025-12-31" \
  -F "license_issued_state=Lagos State" \
  -F "vehicle_make=Toyota" \
  -F "vehicle_model=Corolla" \
  -F "vehicle_year=2020" \
  -F "vehicle_color=Black" \
  -F "vehicle_plate=LAG-123-AB" \
  -F "vehicle_type=Sedan" \
  -F "license_front=@/path/to/license_front.jpg" \
  -F "license_back=@/path/to/license_back.jpg" \
  -F "profile_photo=@/path/to/profile.jpg" \
  -F "vehicle_front=@/path/to/vehicle_front.jpg" \
  -F "vehicle_back=@/path/to/vehicle_back.jpg" \
  -F "vehicle_side=@/path/to/vehicle_side.jpg" \
  -F "vehicle_interior=@/path/to/vehicle_interior.jpg"
```

## Testing
For testing purposes, you can use placeholder images or create a simple test upload form.

## Interactive API Documentation
Visit the interactive API docs for testing:
```
https://afribackend-production-e293.up.railway.app/api/docs/
```