# Admin User Creation Feature Design

## Overview

This feature adds the capability for administrators to create user accounts directly from the admin panel with tier assignment. The system will support Free and Starter subscription tiers with specific feature permissions and API limits enforced across both backend and frontend components.

## Architecture

The feature integrates with the existing admin system and user management infrastructure:

- **Frontend**: Admin Dashboard with new user creation form
- **Backend**: New admin API endpoints for user creation
- **Database**: Existing users table with enhanced tier support
- **Authentication**: Existing admin JWT system for authorization

## Components and Interfaces

### 1. Frontend Components

#### AdminUserCreation Component
- **Location**: `frontend/src/AdminUserCreation.js`
- **Purpose**: Form interface for creating new users
- **Props**: None (standalone component)
- **State**: Form data, validation errors, loading state

#### AdminDashboard Enhancement
- **Location**: `frontend/src/AdminDashboard.js` 
- **Enhancement**: Add "Create User" button and modal integration
- **New State**: User creation modal visibility

### 2. Backend API Endpoints

#### POST /admin/users/create
- **Purpose**: Create new user account with tier assignment
- **Authentication**: Admin JWT required
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword",
    "firstName": "John",
    "lastName": "Doe",
    "subscriptionTier": "starter"
  }
  ```
- **Response**: Created user object with success confirmation

#### GET /admin/users/stats
- **Purpose**: Get user statistics by tier for dashboard
- **Authentication**: Admin JWT required
- **Response**: User counts by tier and status

### 3. Database Schema Updates

The existing `users` table already supports the required fields:
- `subscription_tier` (VARCHAR) - stores 'free' or 'starter'
- `api_calls_limit` (INTEGER) - tier-specific limits
- All other required user fields exist

## Data Models

### User Creation Request
```typescript
interface UserCreationRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  subscriptionTier: 'free' | 'starter';
}
```

### Subscription Tier Configuration
```typescript
interface TierConfig {
  name: 'free' | 'starter';
  apiCallsLimit: number;
  features: {
    batchValidation: boolean;
    emailSending: boolean;
  };
}

const TIER_CONFIGS: Record<string, TierConfig> = {
  free: {
    name: 'free',
    apiCallsLimit: 10,
    features: {
      batchValidation: false,
      emailSending: false
    }
  },
  starter: {
    name: 'starter',
    apiCallsLimit: 10000,
    features: {
      batchValidation: true,
      emailSending: false
    }
  }
};
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: User Creation Completeness
*For any* valid user creation request submitted by an admin, the system should create a complete user record in Supabase with all required fields populated correctly including the specified tier configuration.
**Validates: Requirements 1.2, 1.3**

### Property 2: Tier Configuration Consistency  
*For any* user created with a specific tier, the system should apply the correct API limits and feature permissions that match the tier specification exactly.
**Validates: Requirements 2.2, 2.3, 2.4**

### Property 3: Feature Permission Enforcement
*For any* user logging in with a specific tier, the system should enforce the correct feature access permissions (batch validation and email sending) based on their assigned tier.
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 4: Data Persistence Integrity
*For any* user account created via admin panel, querying the database should return the exact same user data that was submitted in the creation request.
**Validates: Requirements 4.1, 4.2**

### Property 5: Existing User Preservation
*For any* existing user in the system, creating new users via admin panel should not modify or affect their current tier assignments, API usage, or account status.
**Validates: Requirements 4.5**

### Property 6: Admin Feedback Consistency
*For any* user creation attempt, the admin interface should display feedback that accurately reflects the actual database operation result (success with details or specific error message).
**Validates: Requirements 5.3, 5.4**

## Error Handling

### Validation Errors
- **Email Format**: Invalid email format validation
- **Duplicate Email**: Email already exists in system
- **Password Strength**: Minimum password requirements
- **Required Fields**: All fields must be provided

### Database Errors
- **Connection Issues**: Supabase connection failures
- **Constraint Violations**: Database constraint errors
- **Transaction Failures**: Rollback on partial creation

### Authentication Errors
- **Invalid Admin Token**: Expired or invalid JWT
- **Insufficient Permissions**: Admin lacks user creation rights

## Testing Strategy

### Unit Tests
- User creation form validation
- API endpoint request/response handling
- Tier configuration application
- Error message generation

### Property-Based Tests
- **Property 1 Test**: Generate random valid user data, create user, verify complete database record
- **Property 2 Test**: Create users with different tiers, verify correct limits and permissions applied
- **Property 3 Test**: Login as created users, verify feature access matches tier
- **Property 4 Test**: Create user, query database, verify data integrity
- **Property 5 Test**: Create new users while existing users exist, verify no impact on existing accounts
- **Property 6 Test**: Attempt various creation scenarios, verify admin feedback accuracy

### Integration Tests
- End-to-end user creation workflow
- Admin dashboard integration
- User login with created accounts
- Feature access verification for each tier

The testing approach ensures both specific functionality works correctly (unit tests) and that the system maintains correctness across all possible inputs and scenarios (property-based tests).