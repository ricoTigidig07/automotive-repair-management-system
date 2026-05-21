from app.extensions import db

class JobService(db.Model):
    __tablename__ = 'job_service'
    __table_args__ = {'extend_existing': True}
    
    job_id = db.Column(db.Integer, db.ForeignKey('job.job_id'), primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.service_id'), primary_key=True)
    qty = db.Column(db.Integer, default=1)