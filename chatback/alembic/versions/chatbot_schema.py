"""initial chatbot schema

Revision ID: chatbot_schema
Revises: 
Create Date: 2024-03-21 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'chatbot_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_groups_id', 'groups', ['id'])
    op.create_index('ix_groups_name', 'groups', ['name'])

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name='fk_users_group_id_groups'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_sessions_id', 'chat_sessions', ['id'])

    # Create chat role enum
    op.execute("CREATE TYPE chatrole AS ENUM ('USER', 'ASSISTANT', 'SYSTEM')")
    
    # Create conversation state enum
    op.execute("CREATE TYPE conversationstate AS ENUM ('INTERVIEW', 'DOCUMENT', 'COMPLETED')")

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('message_uuid', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('role', postgresql.ENUM('USER', 'ASSISTANT', 'SYSTEM', name='chatrole', create_type=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('message_metadata', postgresql.JSONB, nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_id', 'chat_messages', ['id'])

    # Create chat_state table
    op.create_table(
        'chat_state',
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('current_section', sa.Integer(), nullable=False),
        sa.Column('current_question_index', sa.Integer(), nullable=False),
        sa.Column('state', postgresql.ENUM('INTERVIEW', 'DOCUMENT', 'COMPLETED', name='conversationstate', create_type=False), nullable=False),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('session_id')
    )

def downgrade():
    # Drop tables
    op.drop_table('chat_state')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('users')
    op.drop_table('groups')
    
    # Drop enums
    op.execute('DROP TYPE chatrole')
    op.execute('DROP TYPE conversationstate') 