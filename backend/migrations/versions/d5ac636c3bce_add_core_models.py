"""add core models

Revision ID: d5ac636c3bce
Revises: 
Create Date: 2025-06-20 19:58:25.373249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5ac636c3bce'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('registration_time', sa.DateTime(), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('age', sa.Integer(), nullable=True),
    sa.Column('phone_no', sa.String(length=30), nullable=True),
    sa.Column('gender', sa.String(length=20), nullable=True),
    sa.Column('county', sa.String(length=100), nullable=True),
    sa.Column('town', sa.String(length=100), nullable=True),
    sa.Column('level_of_education', sa.String(length=100), nullable=True),
    sa.Column('profession', sa.String(length=100), nullable=True),
    sa.Column('marital_status', sa.String(length=50), nullable=True),
    sa.Column('religion', sa.String(length=100), nullable=True),
    sa.Column('ethnicity', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('phone_no')
    )
    op.create_table('employees',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('skills', sa.Text(), nullable=True),
    sa.Column('years_of_experience', sa.Integer(), nullable=True),
    sa.Column('expected_salary', sa.Integer(), nullable=True),
    sa.Column('availability', sa.Enum('immediate', 'week', 'month', name='availability'), nullable=True),
    sa.Column('preferred_job_types', sa.String(length=150), nullable=True),
    sa.Column('portfolio_url', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('employers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_name', sa.String(length=150), nullable=True),
    sa.Column('business_type_id', sa.Integer(), nullable=True),
    sa.Column('registration_number', sa.String(length=50), nullable=True),
    sa.Column('company_email', sa.String(length=120), nullable=True),
    sa.Column('company_phone', sa.String(length=30), nullable=True),
    sa.Column('company_location', sa.String(length=150), nullable=True),
    sa.Column('logo_url', sa.String(length=255), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('short_code', sa.Integer(), nullable=True),
    sa.Column('send_time', sa.DateTime(), nullable=True),
    sa.Column('phone_no', sa.String(length=30), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('message_type', sa.Enum('user', 'system', name='messagetype'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ratings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rater_id', sa.Integer(), nullable=True),
    sa.Column('rated_id', sa.Integer(), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['rated_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['rater_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('jobs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('employer_id', sa.Integer(), nullable=True),
    sa.Column('job_title', sa.String(length=150), nullable=True),
    sa.Column('job_description', sa.Text(), nullable=True),
    sa.Column('job_location', sa.String(length=150), nullable=True),
    sa.Column('salary_range', sa.String(length=100), nullable=True),
    sa.Column('employment_type', sa.Enum('full_time', 'part_time', 'casual', name='employmenttype'), nullable=True),
    sa.Column('post_date', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Enum('draft', 'listed', 'filled', 'closed', name='jobstatus'), nullable=True),
    sa.ForeignKeyConstraint(['employer_id'], ['employers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('applications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.Column('employee_id', sa.Integer(), nullable=True),
    sa.Column('application_date', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'shortlisted', 'rejected', 'hired', name='applicationstatus'), nullable=True),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('matches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.Column('employee_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'approved', 'declined', name='matchstatus'), nullable=True),
    sa.Column('matched_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('matches')
    op.drop_table('applications')
    op.drop_table('jobs')
    op.drop_table('ratings')
    op.drop_table('messages')
    op.drop_table('employers')
    op.drop_table('employees')
    op.drop_table('users')
    # ### end Alembic commands ###
