from app import db
from datetime import datetime

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Relationship Information
    relationship_type = db.Column(db.String(50))  # friend, family, colleague, etc.
    company = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    
    # Contact Details
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(10))
    country = db.Column(db.String(50))
    
    # Social Media
    linkedin_url = db.Column(db.String(200))
    twitter_handle = db.Column(db.String(50))
    
    # Additional Info
    notes = db.Column(db.Text)
    birthday = db.Column(db.Date)
    tags = db.Column(db.String(200))  # comma-separated tags
    
    # System fields
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_favorite = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Contact {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def tag_list(self):
        return [tag.strip() for tag in (self.tags or '').split(',') if tag.strip()]
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'relationship_type': self.relationship_type,
            'company': self.company,
            'job_title': self.job_title,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'linkedin_url': self.linkedin_url,
            'twitter_handle': self.twitter_handle,
            'notes': self.notes,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'tags': self.tags,
            'tag_list': self.tag_list,
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
