class Role:
    
    ADMIN = 'admin'
    HR = 'hr'
    MAINTENANCE = 'maintenance'
    CONSTRUCTION = 'construction'
    TOP_MANAGEMENT = 'top management'

    CHOICES = [
        (ADMIN, 'Admin'),
        (HR, 'HR'),
        (MAINTENANCE, 'Maintenance'),
        (CONSTRUCTION, 'Construction'),
        (TOP_MANAGEMENT, 'Top Management')
    ]

    ROLES = [ADMIN, HR, MAINTENANCE, CONSTRUCTION, TOP_MANAGEMENT]


class RequestStatus:

    ACCEPTED = 'accepted'
    REJCTED = 'rejected'
    HOLD_PENDING = 'hold/pending'

    CHOICES = [
        (ACCEPTED, 'Accepted'),
        (REJCTED, 'Rejected'),
        (HOLD_PENDING, 'Hold/Pending')
    ]

    AVAILABLE_CHOICES = [ACCEPTED, REJCTED, HOLD_PENDING]


class Features:

    PURCHASE_REQUEST = 'purchase request'
    PURCHASE_ORDER = 'purchase order'
    PETTY_CASH = 'petty cash'
    DELIVERY_RECORD = 'delivery record'
    VOUCHER_LIQUIDATION = 'voucher liquidation'
