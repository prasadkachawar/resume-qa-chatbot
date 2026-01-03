from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User
from app.models.contact import Contact
from app.services.resume_vector_service import resume_vector_service
import os

bp = Blueprint('api', __name__)

@bp.route('/user')
def get_user():
    """Get user profile data"""
    user = User.query.first()
    if user:
        return jsonify(user.to_dict())
    return jsonify({'error': 'User not found'}), 404

@bp.route('/user', methods=['POST', 'PUT'])
def update_user():
    """Create or update user profile"""
    data = request.get_json()
    
    user = User.query.first()
    if not user:
        user = User()
        db.session.add(user)
    
    # Update user fields from JSON data
    for field in ['first_name', 'last_name', 'email', 'phone', 'street_address', 
                 'city', 'state', 'zip_code', 'country', 'job_title', 'company',
                 'bio', 'linkedin_url', 'github_url', 'website_url']:
        if field in data:
            setattr(user, field, data[field])
    
    try:
        db.session.commit()
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500

@bp.route('/contacts')
def get_contacts():
    """Get all contacts"""
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    search = request.args.get('search', '')
    contacts_query = Contact.query.filter_by(user_id=user.id)
    
    if search:
        contacts_query = contacts_query.filter(
            db.or_(
                Contact.first_name.contains(search),
                Contact.last_name.contains(search),
                Contact.email.contains(search),
                Contact.company.contains(search)
            )
        )
    
    contacts = contacts_query.order_by(Contact.first_name).all()
    return jsonify([contact.to_dict() for contact in contacts])

@bp.route('/contacts', methods=['POST'])
def create_contact():
    """Create new contact"""
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    contact = Contact()
    contact.user_id = user.id
    
    # Update contact fields from JSON data
    for field in ['first_name', 'last_name', 'email', 'phone', 'relationship_type',
                 'company', 'job_title', 'address', 'city', 'state', 'zip_code',
                 'country', 'linkedin_url', 'twitter_handle', 'notes', 'tags']:
        if field in data:
            setattr(contact, field, data[field])
    
    try:
        db.session.add(contact)
        db.session.commit()
        return jsonify(contact.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create contact'}), 500

@bp.route('/contacts/<int:contact_id>')
def get_contact(contact_id):
    """Get specific contact"""
    contact = Contact.query.get_or_404(contact_id)
    return jsonify(contact.to_dict())

@bp.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Update contact"""
    contact = Contact.query.get_or_404(contact_id)
    data = request.get_json()
    
    # Update contact fields from JSON data
    for field in ['first_name', 'last_name', 'email', 'phone', 'relationship_type',
                 'company', 'job_title', 'address', 'city', 'state', 'zip_code',
                 'country', 'linkedin_url', 'twitter_handle', 'notes', 'tags']:
        if field in data:
            setattr(contact, field, data[field])
    
    try:
        db.session.commit()
        return jsonify(contact.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update contact'}), 500

@bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete contact"""
    contact = Contact.query.get_or_404(contact_id)
    
    try:
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'message': 'Contact deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete contact'}), 500

@bp.route('/stats')
def get_stats():
    """Get user statistics"""
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    total_contacts = Contact.query.filter_by(user_id=user.id).count()
    favorite_contacts = Contact.query.filter_by(user_id=user.id, is_favorite=True).count()
    
    # Count contacts by relationship type
    relationship_counts = db.session.query(
        Contact.relationship_type, db.func.count(Contact.id)
    ).filter_by(user_id=user.id).group_by(Contact.relationship_type).all()
    
    return jsonify({
        'total_contacts': total_contacts,
        'favorite_contacts': favorite_contacts,
        'relationship_breakdown': dict(relationship_counts)
    })

# Resume Vector Processing Endpoints

@bp.route('/resume/process', methods=['POST'])
def process_resume():
    """Process resume PDF and create vectors"""
    try:
        data = request.get_json()
        
        # Get parameters with defaults
        pdf_filename = data.get('pdf_filename', 'Prassad Narayan Kachawar GResume .docx.pdf')
        chunk_size = data.get('chunk_size', 100)
        overlap = data.get('overlap', 10)
        
        # Build full path to PDF file
        pdf_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', pdf_filename)
        
        # Process the resume
        result = resume_vector_service.process_resume_pdf(pdf_path, chunk_size, overlap)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to process resume'
        }), 500

@bp.route('/resume/search', methods=['POST'])
def search_resume():
    """Search resume content using semantic search"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        n_results = data.get('n_results', 5)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter is required',
                'message': 'Please provide a search query'
            }), 400
        
        result = resume_vector_service.search_resume_content(query, n_results)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to search resume content'
        }), 500

@bp.route('/resume/stats')
def get_resume_stats():
    """Get statistics about stored resume vectors"""
    try:
        result = resume_vector_service.get_resume_stats()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to get resume statistics'
        }), 500

@bp.route('/resume/clear', methods=['DELETE'])
def clear_resume_vectors():
    """Clear all resume vectors"""
    try:
        result = resume_vector_service.clear_resume_vectors()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to clear resume vectors'
        }), 500

@bp.route('/resume/reprocess', methods=['POST'])
def reprocess_resume():
    """Clear existing vectors and reprocess resume"""
    try:
        data = request.get_json() or {}
        
        pdf_filename = data.get('pdf_filename', 'Prassad Narayan Kachawar GResume .docx.pdf')
        chunk_size = data.get('chunk_size', 100)
        overlap = data.get('overlap', 10)
        
        # Build full path to PDF file
        pdf_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', pdf_filename)
        
        result = resume_vector_service.reprocess_resume(pdf_path, chunk_size, overlap)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to reprocess resume'
        }), 500
