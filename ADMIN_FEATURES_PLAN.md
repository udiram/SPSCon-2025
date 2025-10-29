# 🎯 Admin Panel & User Change Requests - Implementation Plan

## Overview
Comprehensive admin panel with user management, change request handling, and system monitoring.

## Database Changes

### ✅ New Model: ChangeRequest
```python
class ChangeRequest(db.Model):
    - id: Primary key
    - user_id: Who requested the change
    - request_type: Type of change (email, username, name, other)
    - field_name: Which field to modify
    - current_value: Current value
    - proposed_value: What they want it changed to
    - reason: Why they want the change
    - status: pending/approved/denied
    - admin_notes: Admin's response
    - timestamps: created_at, updated_at, reviewed_at
    - reviewed_by: Which admin handled it
```

## Features to Implement

### 1. Settings Page Enhancements

#### A. Account Information Section (NEW)
```
- Show current registration details
- Email, Username, First Name, Last Name
- Joined date
- Last login
- Account status
```

#### B. Request Change Functionality (NEW)
```
- "Request Change" button for each field
- Modal form with:
  - Field to change (dropdown)
  - Current value (read-only)
  - Proposed new value (input)
  - Reason (textarea, required)
- Submit to admin for review
- View your pending requests
```

### 2. Comprehensive Admin Panel

#### A. Dashboard Overview
```
- System Statistics:
  ├─ Total Users
  ├─ Active Users (last 7 days)
  ├─ Total Posters
  ├─ Total Visits
  ├─ Pending Change Requests
  └─ System Health

- Quick Actions:
  ├─ Review Change Requests
  ├─ Manage Users
  ├─ Manage Posters
  ├─ View Analytics
  └─ System Settings
```

#### B. Change Request Management
```
- List all change requests with filters:
  ├─ Status (pending/approved/denied)
  ├─ Type (email/username/name/other)
  ├─ Date range
  └─ User search

- For each request show:
  ├─ User info
  ├─ What they want to change
  ├─ Current → Proposed
  ├─ Their reason
  ├─ Request date
  └─ Actions (Approve/Deny/Add Notes)

- Approve flow:
  ├─ Show confirmation with changes
  ├─ Optional admin notes
  ├─ Apply changes to database
  ├─ Notify user (email if enabled)

- Deny flow:
  ├─ Require reason for denial
  ├─ Optional admin notes
  ├─ Notify user
```

#### C. User Management
```
- User List with search/filter:
  ├─ Search by name, email, username
  ├─ Filter by registration date
  ├─ Filter by activity status
  └─ Sort by various fields

- For each user:
  ├─ Basic info (email, username, name)
  ├─ Registration date
  ├─ Last active
  ├─ Stats (favorites, visits, posters)
  ├─ Actions:
      ├─ View details
      ├─ Edit user info
      ├─ Reset password
      ├─ Disable/Enable account
      └─ Delete user

- Bulk actions:
  ├─ Export user list
  ├─ Send announcement email
  └─ Bulk disable/enable
```

#### D. Poster Management
```
- Poster List with search/filter:
  ├─ Search by number, title, author
  ├─ Filter by session, category, institution
  ├─ Sort by visits, favorites
  └─ Show QR code status

- For each poster:
  ├─ Basic info
  ├─ Presenter assignment
  ├─ Visit count
  ├─ Favorite count
  ├─ Actions:
      ├─ Edit poster details
      ├─ Regenerate QR code
      ├─ Assign/Unassign presenter
      ├─ Delete poster

- Bulk actions:
  ├─ Export poster data
  ├─ Regenerate all QR codes
  ├─ Auto-assign presenters
  └─ Unassign all
```

#### E. Analytics & Monitoring
```
- Real-time Statistics:
  ├─ Active users online
  ├─ Recent activity feed
  ├─ Popular posters
  ├─ Search trends
  └─ Error logs

- Engagement Metrics:
  ├─ Daily active users chart
  ├─ Visits over time
  ├─ Top institutions
  ├─ Category distribution
  └─ Peak usage times

- System Health:
  ├─ Database size
  ├─ Response times
  ├─ Error rate
  └─ Uptime
```

#### F. System Settings
```
- Conference Settings:
  ├─ Conference name
  ├─ Dates and times
  ├─ Location
  └─ Registration status

- Email Settings:
  ├─ SMTP configuration
  ├─ Email templates
  └─ Notification preferences

- Feature Flags:
  ├─ Enable/disable recommendations
  ├─ Enable/disable registrations
  ├─ Maintenance mode
  └─ API access

- Security Settings:
  ├─ Password requirements
  ├─ Session timeout
  ├─ Rate limiting
  └─ IP whitelist
```

## API Endpoints to Add

### Change Request APIs
```
POST   /api/change-request          - Submit new change request
GET    /api/change-requests          - Get user's change requests
GET    /api/admin/change-requests    - Get all change requests (admin)
POST   /api/admin/change-request/:id/approve  - Approve request
POST   /api/admin/change-request/:id/deny     - Deny request
PUT    /api/admin/change-request/:id/notes    - Update admin notes
```

### User Management APIs
```
GET    /api/admin/users              - List all users
GET    /api/admin/users/:id          - Get user details
PUT    /api/admin/users/:id          - Update user
DELETE /api/admin/users/:id          - Delete user
POST   /api/admin/users/:id/disable  - Disable user account
POST   /api/admin/users/:id/enable   - Enable user account
POST   /api/admin/users/:id/reset-password - Reset password
```

### Poster Management APIs
```
GET    /api/admin/posters            - List all posters
GET    /api/admin/posters/:id        - Get poster details
PUT    /api/admin/posters/:id        - Update poster
DELETE /api/admin/posters/:id        - Delete poster
POST   /api/admin/posters/:id/regenerate-qr - Regenerate QR code
```

### System APIs
```
GET    /api/admin/stats              - System statistics
GET    /api/admin/activity           - Recent activity
GET    /api/admin/health             - System health check
POST   /api/admin/maintenance        - Toggle maintenance mode
```

## UI/UX Design

### Settings Page Layout
```
┌──────────────────────────────────────┐
│ Settings                              │
├──────────────────────────────────────┤
│ ┌────────┐ ┌───────────────────────┐│
│ │ Nav    │ │ Account Information   ││
│ │        │ │ ┌───────────────────┐ ││
│ │ Account│ │ │ Email: user@...   │ ││
│ │ Appear │ │ │ Username: john    │ ││
│ │ Privacy│ │ │ Name: John Doe    │ ││
│ │ Data   │ │ │                   │ ││
│ │        │ │ │ [Request Change]  │ ││
│ │        │ │ └───────────────────┘ ││
│ │        │ │                       ││
│ │        │ │ My Change Requests    ││
│ │        │ │ ┌───────────────────┐ ││
│ │        │ │ │ Pending: 2        │ ││
│ │        │ │ │ [View Details]    │ ││
│ │        │ │ └───────────────────┘ ││
│ └────────┘ └───────────────────────┘│
└──────────────────────────────────────┘
```

### Admin Panel Layout
```
┌──────────────────────────────────────────────┐
│ Admin Panel              👤 Admin ▼          │
├──────────────────────────────────────────────┤
│ ┌────────────┐ ┌──────────────────────────┐ │
│ │ Dashboard  │ │ System Overview          │ │
│ │ Requests   │ │ ┌────┐ ┌────┐ ┌────┐    │ │
│ │ Users      │ │ │354 │ │ 12 │ │ 3  │    │ │
│ │ Posters    │ │ │Post│ │User│ │Req │    │ │
│ │ Analytics  │ │ └────┘ └────┘ └────┘    │ │
│ │ Settings   │ │                          │ │
│ │            │ │ Pending Change Requests  │ │
│ │            │ │ ┌──────────────────────┐ │ │
│ │            │ │ │ John wants to change │ │ │
│ │            │ │ │ email: john@old.com  │ │ │
│ │            │ │ │     → john@new.com   │ │ │
│ │            │ │ │ Reason: Graduated    │ │ │
│ │            │ │ │ [Approve] [Deny]     │ │ │
│ │            │ │ └──────────────────────┘ │ │
│ └────────────┘ └──────────────────────────┘ │
└──────────────────────────────────────────────┘
```

## Implementation Order

1. ✅ **Model Creation** - ChangeRequest model added
2. 🔄 **Database Migration** - Create migration script
3. ⏳ **Settings Page** - Add account info & change request form
4. ⏳ **Change Request APIs** - Backend endpoints
5. ⏳ **Admin Dashboard** - Main layout & navigation
6. ⏳ **Change Request Management** - Admin review interface
7. ⏳ **User Management** - User list & actions
8. ⏳ **Poster Management** - Enhanced poster admin
9. ⏳ **Analytics Dashboard** - Stats & monitoring
10. ⏳ **Testing & Polish** - Test all features

## Next Steps

Run the migration to add the ChangeRequest table:
```bash
python migrate_db.py
```

Then the implementation will continue with each feature being added incrementally.

---

**Estimated Total Implementation**: ~2-3 hours
**Complexity**: High
**Impact**: High - Major feature addition for admin and users

