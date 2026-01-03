from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.user import User
from app.models.contact import Contact

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Dashboard - Main page showing overview of user info and recent contacts"""
    user = User.query.first()
    recent_contacts = Contact.query.filter_by(user_id=user.id).order_by(Contact.updated_at.desc()).limit(5).all() if user else []
    total_contacts = Contact.query.filter_by(user_id=user.id).count() if user else 0
    
    return render_template('index.html', 
                         user=user, 
                         recent_contacts=recent_contacts,
                         total_contacts=total_contacts)

@bp.route('/profile')
def profile():
    """User profile page"""
    user = User.query.first()
    return render_template('profile.html', user=user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile"""
    user = User.query.first()
    
    if request.method == 'POST':
        if not user:
            user = User()
            db.session.add(user)
        
        # Update user fields from form data
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.email = request.form.get('email', '').strip()
        user.phone = request.form.get('phone', '').strip()
        user.street_address = request.form.get('street_address', '').strip()
        user.city = request.form.get('city', '').strip()
        user.state = request.form.get('state', '').strip()
        user.zip_code = request.form.get('zip_code', '').strip()
        user.country = request.form.get('country', '').strip()
        user.job_title = request.form.get('job_title', '').strip()
        user.company = request.form.get('company', '').strip()
        user.bio = request.form.get('bio', '').strip()
        user.linkedin_url = request.form.get('linkedin_url', '').strip()
        user.github_url = request.form.get('github_url', '').strip()
        user.website_url = request.form.get('website_url', '').strip()
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
    
    return render_template('edit_profile.html', user=user)

@bp.route('/contacts')
def contacts():
    """Contacts list page"""
    user = User.query.first()
    if not user:
        flash('Please create your profile first.', 'warning')
        return redirect(url_for('main.edit_profile'))
    
    search_query = request.args.get('search', '').strip()
    contacts_query = Contact.query.filter_by(user_id=user.id)
    
    if search_query:
        contacts_query = contacts_query.filter(
            db.or_(
                Contact.first_name.contains(search_query),
                Contact.last_name.contains(search_query),
                Contact.email.contains(search_query),
                Contact.company.contains(search_query)
            )
        )
    
    contacts = contacts_query.order_by(Contact.first_name).all()
    return render_template('contacts.html', contacts=contacts, search_query=search_query)

@bp.route('/contacts/add', methods=['GET', 'POST'])
def add_contact():
    """Add new contact"""
    user = User.query.first()
    if not user:
        flash('Please create your profile first.', 'warning')
        return redirect(url_for('main.edit_profile'))
    
    if request.method == 'POST':
        contact = Contact()
        contact.user_id = user.id
        contact.first_name = request.form.get('first_name', '').strip()
        contact.last_name = request.form.get('last_name', '').strip()
        contact.email = request.form.get('email', '').strip()
        contact.phone = request.form.get('phone', '').strip()
        contact.relationship_type = request.form.get('relationship_type', '').strip()
        contact.company = request.form.get('company', '').strip()
        contact.job_title = request.form.get('job_title', '').strip()
        contact.notes = request.form.get('notes', '').strip()
        contact.tags = request.form.get('tags', '').strip()
        
        try:
            db.session.add(contact)
            db.session.commit()
            flash('Contact added successfully!', 'success')
            return redirect(url_for('main.contacts'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding contact. Please try again.', 'error')
    
    return render_template('add_contact.html')

@bp.route('/contacts/<int:contact_id>')
def view_contact(contact_id):
    """View contact details"""
    contact = Contact.query.get_or_404(contact_id)
    return render_template('view_contact.html', contact=contact)

@bp.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
def edit_contact(contact_id):
    """Edit contact"""
    contact = Contact.query.get_or_404(contact_id)
    
    if request.method == 'POST':
        contact.first_name = request.form.get('first_name', '').strip()
        contact.last_name = request.form.get('last_name', '').strip()
        contact.email = request.form.get('email', '').strip()
        contact.phone = request.form.get('phone', '').strip()
        contact.relationship_type = request.form.get('relationship_type', '').strip()
        contact.company = request.form.get('company', '').strip()
        contact.job_title = request.form.get('job_title', '').strip()
        contact.notes = request.form.get('notes', '').strip()
        contact.tags = request.form.get('tags', '').strip()
        
        try:
            db.session.commit()
            flash('Contact updated successfully!', 'success')
            return redirect(url_for('main.view_contact', contact_id=contact.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating contact. Please try again.', 'error')
    
    return render_template('edit_contact.html', contact=contact)

@bp.route('/contacts/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    """Delete contact"""
    contact = Contact.query.get_or_404(contact_id)
    
    try:
        db.session.delete(contact)
        db.session.commit()
        flash('Contact deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting contact. Please try again.', 'error')
    
    return redirect(url_for('main.contacts'))

@bp.route('/resume-qa')
def resume_qa():
    """Resume Question & Answer page"""
    return render_template('resume_qa.html')
