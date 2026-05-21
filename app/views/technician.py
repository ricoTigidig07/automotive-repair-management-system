"""
Technician Routes Blueprint
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from datetime import date, datetime, timedelta
import logging
from app.utils.decorators import handle_database_errors, log_function_call
from app.utils.validators import sanitize_input
from app.services.customer_service import CustomerService
from app.services.job_service import JobService
from app.services.billing_service import BillingService

# Create blueprint
technician_bp = Blueprint('technician', __name__)
logger = logging.getLogger(__name__)

# Initialize services
customer_service = CustomerService()
job_service = JobService()
billing_service = BillingService()


def require_technician_login():
    """Check technician login status"""
    if not session.get('logged_in'):
        flash('Please login first', 'warning')
        return redirect(url_for('auth.login'))
    
    # Allow superadmin, admin, owner, technician
    role = session.get('current_role')
    if role not in ('technician', 'owner', 'admin'):
        # Also check if user is superadmin from database
        from app.models.user import User
        user = User.query.get(session.get('user_id'))
        if user and user.is_superadmin:
            session['current_role'] = 'owner'
            return None
        
        flash('Technician privileges required', 'error')
        return redirect(url_for('main.index'))
    
    return None


@technician_bp.route('/dashboard')
@handle_database_errors
@log_function_call
def dashboard():
    """Technician dashboard"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        from app.models.job import Job
        from app.models.customer import Customer
        from app.extensions import db
        from sqlalchemy import func
        
        tenant_id = session.get('current_tenant_id', 1)
        
        # Get statistics
        active_jobs = Job.query.filter_by(tenant_id=tenant_id, completed=False).count()
        
        # Jobs this week
        week_start = date.today() - timedelta(days=date.today().weekday())
        jobs_this_week = Job.query.filter(
            Job.tenant_id == tenant_id,
            Job.job_date >= week_start
        ).count()
        
        # Total value of active jobs
        total_value = db.session.query(func.sum(Job.total_cost)).filter(
            Job.tenant_id == tenant_id,
            Job.completed == False
        ).scalar() or 0
        
        # Unpaid jobs
        unpaid_jobs = Job.query.filter_by(tenant_id=tenant_id, paid=False).count()
        
        # Get recent jobs
        recent_jobs = db.session.query(
            Job.job_id,
            Job.job_date,
            Job.total_cost,
            Job.completed,
            Job.paid,
            Customer.first_name,
            Customer.family_name,
            Customer.customer_id
        ).join(Customer, Job.customer == Customer.customer_id).filter(
            Job.tenant_id == tenant_id
        ).order_by(Job.job_date.desc()).limit(10).all()
        
        return render_template('technician/dashboard.html',
                             active_jobs=active_jobs,
                             jobs_this_week=jobs_this_week,
                             total_value=float(total_value),
                             unpaid_jobs=unpaid_jobs,
                             recent_jobs=recent_jobs,
                             today=date.today())
                             
    except Exception as e:
        logger.error(f"Failed to load technician dashboard: {e}")
        flash('Failed to load dashboard', 'error')
        return render_template('technician/dashboard.html',
                             active_jobs=0,
                             jobs_this_week=0,
                             total_value=0,
                             unpaid_jobs=0,
                             recent_jobs=[],
                             today=date.today())


@technician_bp.route('/api/job/<int:job_id>')
def api_job_details(job_id):
    """API endpoint for job details"""
    from app.models.job import Job
    from app.models.customer import Customer
    
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'})
    
    customer = Customer.query.get(job.customer)
    
    return jsonify({
        'success': True,
        'job': {
            'job_id': job.job_id,
            'job_date': job.job_date.strftime('%Y-%m-%d'),
            'total_cost': float(job.total_cost),
            'completed': job.completed,
            'paid': job.paid
        },
        'customer': {
            'first_name': customer.first_name,
            'family_name': customer.family_name,
            'phone': customer.phone,
            'email': customer.email
        }
    })


@technician_bp.route('/api/job/<int:job_id>/pay', methods=['POST'])
def api_mark_paid(job_id):
    """API endpoint to mark job as paid"""
    from app.models.job import Job
    from app.extensions import db
    
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'})
    
    job.paid = True
    db.session.commit()
    
    return jsonify({'success': True})


@technician_bp.route('/current-jobs')
@handle_database_errors
@log_function_call
def current_jobs():
    """View current/active jobs"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        from app.models.job import Job
        from app.models.customer import Customer
        from app.extensions import db
        
        tenant_id = session.get('current_tenant_id', 1)
        
        # Get pagination page
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get filter parameters
        search_query = sanitize_input(request.args.get('search', ''))
        status_filter = sanitize_input(request.args.get('status', 'all'))
        sort_by = sanitize_input(request.args.get('sort', 'date_desc'))
        
        # Build query
        query = db.session.query(
            Job.job_id,
            Job.job_date,
            Job.total_cost,
            Job.completed,
            Job.paid,
            Customer.first_name,
            Customer.family_name,
            Customer.customer_id,
            Customer.phone,
            Customer.email
        ).join(Customer, Job.customer == Customer.customer_id).filter(
            Job.tenant_id == tenant_id
        )
        
        # Apply status filter
        if status_filter == 'active':
            query = query.filter(Job.completed == False)
        elif status_filter == 'completed':
            query = query.filter(Job.completed == True)
        elif status_filter == 'unpaid':
            query = query.filter(Job.paid == False)
        
        # Apply search
        if search_query:
            query = query.filter(
                db.or_(
                    Customer.first_name.ilike(f'%{search_query}%'),
                    Customer.family_name.ilike(f'%{search_query}%'),
                    Customer.email.ilike(f'%{search_query}%')
                )
            )
        
        # Apply sorting
        if sort_by == 'date_asc':
            query = query.order_by(Job.job_date.asc())
        elif sort_by == 'date_desc':
            query = query.order_by(Job.job_date.desc())
        elif sort_by == 'cost_high':
            query = query.order_by(Job.total_cost.desc())
        elif sort_by == 'cost_low':
            query = query.order_by(Job.total_cost.asc())
        else:
            query = query.order_by(Job.job_date.desc())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        jobs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Calculate statistics (for all jobs, not just current page)
        all_jobs = db.session.query(
            Job.job_id,
            Job.completed,
            Job.paid,
            Job.total_cost,
            Job.job_date
        ).filter(Job.tenant_id == tenant_id).all()
        
        active_count = len([j for j in all_jobs if not j.completed])
        this_week_count = len([j for j in all_jobs if j.job_date and j.job_date >= date.today() - timedelta(days=7)])
        total_value = sum(float(j.total_cost) for j in all_jobs)
        unpaid_count = len([j for j in all_jobs if not j.paid])
        
        return render_template('technician/current_jobs.html',
                             jobs=jobs,
                             active_count=active_count,
                             this_week_count=this_week_count,
                             total_value=total_value,
                             unpaid_count=unpaid_count,
                             page=page,
                             search_query=search_query,
                             status_filter=status_filter,
                             sort_by=sort_by,
                             today=date.today())
                             
    except Exception as e:
        logger.error(f"Failed to load current jobs: {e}")
        flash('Failed to load jobs', 'error')
        return render_template('technician/current_jobs.html',
                             jobs=[],
                             active_count=0,
                             this_week_count=0,
                             total_value=0,
                             unpaid_count=0,
                             page=1,
                             search_query='',
                             status_filter='all',
                             sort_by='date_desc',
                             today=date.today())


@technician_bp.route('/modify-job/<int:job_id>', methods=['GET', 'POST'])
@handle_database_errors
@log_function_call
def modify_job(job_id):
    """Modify a specific job (add services/parts)"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        from app.models.job import Job
        from app.models.customer import Customer
        from app.models.service import Service
        from app.models.part import Part
        from app.models.job_service import JobService as JobServiceModel
        from app.models.job_part import JobPart
        from app.extensions import db
        
        tenant_id = session.get('current_tenant_id', 1)
        
        job = db.session.query(Job, Customer).join(Customer, Job.customer == Customer.customer_id).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            flash('Job not found', 'error')
            return redirect(url_for('technician.current_jobs'))
        
        job_obj, customer = job
        
        # Get available services and parts
        services = Service.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        parts = Part.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        
        # Get assigned services for this job
        assigned_services = db.session.query(JobServiceModel, Service).join(
            Service, JobServiceModel.service_id == Service.service_id
        ).filter(JobServiceModel.job_id == job_id).all()
        
        # Get assigned parts for this job
        assigned_parts = db.session.query(JobPart, Part).join(
            Part, JobPart.part_id == Part.part_id
        ).filter(JobPart.job_id == job_id).all()
        
        if request.method == 'POST':
            # Handle adding service
            if 'add_service' in request.form:
                service_id = request.form.get('service_id')
                if service_id:
                    service = Service.query.get(service_id)
                    if service:
                        existing = JobServiceModel.query.filter_by(job_id=job_id, service_id=service_id).first()
                        if not existing:
                            job_service = JobServiceModel(job_id=job_id, service_id=service_id, qty=1)
                            db.session.add(job_service)
                            # Update total cost
                            job_obj.total_cost = float(job_obj.total_cost or 0) + float(service.cost)
                            db.session.commit()
                            flash(f'Service "{service.service_name}" added!', 'success')
                        else:
                            flash('Service already added', 'warning')
            
            # Handle adding part
            elif 'add_part' in request.form:
                part_id = request.form.get('part_id')
                if part_id:
                    part = Part.query.get(part_id)
                    if part:
                        existing = JobPart.query.filter_by(job_id=job_id, part_id=part_id).first()
                        if not existing:
                            job_part = JobPart(job_id=job_id, part_id=part_id, qty=1)
                            db.session.add(job_part)
                            job_obj.total_cost = float(job_obj.total_cost or 0) + float(part.cost)
                            db.session.commit()
                            flash(f'Part "{part.part_name}" added!', 'success')
                        else:
                            flash('Part already added', 'warning')
            
            # Handle remove service
            elif 'remove_service' in request.form:
                job_service_id = request.form.get('job_service_id')
                job_service = JobServiceModel.query.get(job_service_id)
                if job_service:
                    service = Service.query.get(job_service.service_id)
                    job_obj.total_cost = float(job_obj.total_cost or 0) - float(service.cost)
                    db.session.delete(job_service)
                    db.session.commit()
                    flash('Service removed', 'success')
            
            # Handle remove part
            elif 'remove_part' in request.form:
                job_part_id = request.form.get('job_part_id')
                job_part = JobPart.query.get(job_part_id)
                if job_part:
                    part = Part.query.get(job_part.part_id)
                    job_obj.total_cost = float(job_obj.total_cost or 0) - float(part.cost)
                    db.session.delete(job_part)
                    db.session.commit()
                    flash('Part removed', 'success')
            
            # Handle complete job
            elif 'complete_job' in request.form:
                job_obj.completed = True
                db.session.commit()
                flash('Job marked as completed!', 'success')
                return redirect(url_for('technician.current_jobs'))
            
            return redirect(url_for('technician.modify_job', job_id=job_id))
        
        return render_template('technician/modify_job.html',
                             job=job_obj,
                             customer=customer,
                             services=services,
                             parts=parts,
                             assigned_services=assigned_services,
                             assigned_parts=assigned_parts)
                             
    except Exception as e:
        logger.error(f"Failed to modify job: {e}")
        flash('Failed to load job details', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/new-job', methods=['GET', 'POST'])
def new_job():
    """Create a new job/repair order"""
    if not session.get('logged_in'):
        flash('Please login first', 'warning')
        return redirect(url_for('auth.login'))
    
    from app.models.job import Job
    from app.models.customer import Customer
    from app.extensions import db
    from datetime import datetime, date
    
    tenant_id = session.get('current_tenant_id', 1)
    # REMOVED is_active=True
    customers = Customer.query.filter_by(tenant_id=tenant_id).all()
    
    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            job_date = request.form.get('job_date')
            
            if not customer_id or not job_date:
                flash('Please select customer and job date', 'error')
                return redirect(url_for('technician.new_job'))
            
            job = Job(
                tenant_id=tenant_id,
                customer=int(customer_id),
                job_date=datetime.strptime(job_date, '%Y-%m-%d').date(),
                total_cost=0.00,
                completed=False,
                paid=False
            )
            db.session.add(job)
            db.session.commit()
            
            flash('New job created successfully!', 'success')
            return redirect(url_for('technician.modify_job', job_id=job.job_id))
            
        except Exception as e:
            print(f"Error: {e}")
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('technician.new_job'))
    
    return render_template('technician/new_job.html', customers=customers, today=date.today())