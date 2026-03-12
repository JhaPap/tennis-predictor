from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String
)
from sqlalchemy.orm import relationship
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id                        = Column(Integer, primary_key=True, index=True)
    email                     = Column(String, unique=True, index=True, nullable=False)
    username                  = Column(String, unique=True, index=True, nullable=False)
    hashed_password           = Column(String, nullable=False)
    is_email_verified         = Column(Boolean, default=False, nullable=False)
    verification_token        = Column(String, nullable=True, index=True)
    verification_token_expires = Column(DateTime, nullable=True)
    created_at                = Column(DateTime, default=datetime.utcnow)


class Player(Base):
    __tablename__ = "players"

    id               = Column(Integer, primary_key=True, index=True)
    name             = Column(String, unique=True, index=True, nullable=False)
    elo_overall      = Column(Float, default=1500.0)
    elo_hard         = Column(Float, default=1500.0)
    elo_clay         = Column(Float, default=1500.0)
    elo_grass        = Column(Float, default=1500.0)
    matches_played   = Column(Integer, default=0)
    wins             = Column(Integer, default=0)
    win_rate_hard    = Column(Float, default=0.5)
    win_rate_clay    = Column(Float, default=0.5)
    win_rate_grass   = Column(Float, default=0.5)
    win_rate_overall = Column(Float, default=0.5)
    matches_hard     = Column(Integer, default=0)
    matches_clay     = Column(Integer, default=0)
    matches_grass    = Column(Integer, default=0)
    current_rank     = Column(Integer, nullable=True)
    current_pts      = Column(Float, nullable=True)

    matches_as_p1 = relationship("Match", foreign_keys="Match.player1_id", back_populates="player1")
    matches_as_p2 = relationship("Match", foreign_keys="Match.player2_id", back_populates="player2")


class Match(Base):
    __tablename__ = "matches"

    id          = Column(Integer, primary_key=True, index=True)
    tournament  = Column(String, index=True)
    date        = Column(Date, index=True)
    series      = Column(String)
    court       = Column(String)
    surface     = Column(String, index=True)
    round       = Column(String)
    best_of     = Column(Integer)

    player1_id  = Column(Integer, ForeignKey("players.id"), index=True)
    player2_id  = Column(Integer, ForeignKey("players.id"), index=True)
    winner_id   = Column(Integer, ForeignKey("players.id"), index=True)

    rank1       = Column(Integer, nullable=True)
    rank2       = Column(Integer, nullable=True)
    pts1        = Column(Float, nullable=True)
    pts2        = Column(Float, nullable=True)
    odd1        = Column(Float, nullable=True)
    odd2        = Column(Float, nullable=True)
    score       = Column(String, nullable=True)

    elo_p1_before         = Column(Float, nullable=True)
    elo_p2_before         = Column(Float, nullable=True)
    elo_surface_p1_before = Column(Float, nullable=True)
    elo_surface_p2_before = Column(Float, nullable=True)

    player1 = relationship("Player", foreign_keys=[player1_id], back_populates="matches_as_p1")
    player2 = relationship("Player", foreign_keys=[player2_id], back_populates="matches_as_p2")


class PredictionLog(Base):
    __tablename__ = "prediction_log"

    id               = Column(Integer, primary_key=True, index=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    player1_id       = Column(Integer, ForeignKey("players.id"))
    player2_id       = Column(Integer, ForeignKey("players.id"))
    player1_name     = Column(String)
    player2_name     = Column(String)
    surface          = Column(String)
    series           = Column(String)
    best_of          = Column(Integer)
    round            = Column(String, nullable=True)
    p1_win_prob      = Column(Float)
    actual_winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    was_correct      = Column(Boolean, nullable=True)
