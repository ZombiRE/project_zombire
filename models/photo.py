from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from sqlalchemy.orm import Session
from .database import Base, db_session


class Photo(Base):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True)
    file_path = Column(String(255), nullable=False)
    telegram_user_id = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def create(cls, file_path, telegram_user_id, description=None, status='pending'):
        photo = cls(
            file_path=file_path,
            telegram_user_id=telegram_user_id,
            description=description,
            status=status
        )
        db_session.add(photo)
        db_session.commit()
        return photo

    @classmethod
    def get_by_id(cls, photo_id):
        return cls.query.get(photo_id)

    @classmethod
    def get_approved_photos(cls):
        return cls.query.filter_by(status='approved').order_by(cls.created_at.desc()).all()

    def approve(self):
        self.status = 'approved'
        db_session.commit()

    def reject(self):
        self.status = 'rejected'
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'file_path': self.file_path,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
