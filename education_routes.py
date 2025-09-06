"""
Education module functionality for Antidote platform.

This module provides contextual health education with gamification features
to help users learn about their medical procedures and related health topics.
"""

import os
import json
import logging
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from models import (
    User, Procedure, EducationModule, ModuleQuiz as Quiz, QuizQuestion, 
    UserAchievement, QuizAttempt as UserQuizAttempt
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Blueprint
education = Blueprint('education', __name__, url_prefix='/learn')


# Routes for the education module
@education.route('/')
def learn_home():
    """Education module home page."""
    try:
        # Get featured modules
        featured_modules = EducationModule.query.order_by(func.random()).limit(6).all()
        
        # Get modules by level
        beginner_modules = EducationModule.query.filter(EducationModule.level <= 2).limit(4).all()
        intermediate_modules = EducationModule.query.filter(EducationModule.level.between(3, 4)).limit(4).all()
        advanced_modules = EducationModule.query.filter(EducationModule.level >= 5).limit(4).all()
        
        # Get user's latest achievements if logged in
        user_achievements = []
        completed_modules = []
        if current_user.is_authenticated:
            user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).order_by(UserAchievement.achieved_at.desc()).limit(5).all()
            
            # Get completed modules
            completed_module_ids = db.session.query(UserAchievement.module_id).filter_by(
                user_id=current_user.id, 
                achievement_type='module_completed'
            ).all()
            completed_modules = [module_id for (module_id,) in completed_module_ids]
        
        return render_template(
            'education/index.html',
            featured_modules=featured_modules,
            beginner_modules=beginner_modules,
            intermediate_modules=intermediate_modules,
            advanced_modules=advanced_modules,
            user_achievements=user_achievements,
            completed_modules=completed_modules
        )
    except Exception as e:
        logger.error(f"Error rendering education home page: {str(e)}")
        return render_template('education/index.html', error=str(e))


@education.route('/browse')
def browse_modules():
    """Browse all education modules."""
    try:
        # Get filter parameters
        procedure_id = request.args.get('procedure_id', type=int)
        level = request.args.get('level', type=int)
        search = request.args.get('search', '')
        
        # Base query
        query = EducationModule.query
        
        # Default value for procedure name
        procedure_name = None
        
        # Apply filters
        if procedure_id:
            query = query.filter_by(procedure_id=procedure_id)
            # Get procedure for title
            procedure = Procedure.query.get(procedure_id)
            if procedure:
                procedure_name = procedure.procedure_name
        
        if level:
            query = query.filter_by(level=level)
        
        if search:
            query = query.filter(
                EducationModule.title.ilike(f'%{search}%') | 
                EducationModule.description.ilike(f'%{search}%')
            )
        
        # Get all modules with applied filters
        modules = query.order_by(EducationModule.level, EducationModule.title).all()
        
        # Get user's completed modules if logged in
        completed_modules = []
        if current_user.is_authenticated:
            completed_module_ids = db.session.query(UserAchievement.module_id).filter_by(
                user_id=current_user.id, 
                achievement_type='module_completed'
            ).all()
            completed_modules = [module_id for (module_id,) in completed_module_ids]
        
        # Get all procedures for filter dropdown
        procedures = Procedure.query.all()
        
        return render_template(
            'education/browse.html',
            modules=modules,
            procedures=procedures,
            procedure_id=procedure_id,
            procedure_name=procedure_name,
            level=level,
            search=search,
            completed_modules=completed_modules
        )
    except Exception as e:
        logger.error(f"Error browsing education modules: {str(e)}")
        return render_template('education/browse.html', error=str(e), modules=[])


@education.route('/module/<int:module_id>')
def view_module(module_id):
    """View an education module."""
    try:
        module = EducationModule.query.get_or_404(module_id)
        
        # Get quizzes for this module
        quizzes = Quiz.query.filter_by(module_id=module.id).all()
        
        # Check if user has completed this module
        module_completed = False
        quiz_results = {}
        
        if current_user.is_authenticated:
            # Check for module completion achievement
            completion = UserAchievement.query.filter_by(
                user_id=current_user.id,
                module_id=module.id,
                achievement_type='module_completed'
            ).first()
            
            module_completed = completion is not None
            
            # Get quiz attempt results
            for quiz in quizzes:
                attempt = UserQuizAttempt.query.filter_by(
                    user_id=current_user.id,
                    quiz_id=quiz.id
                ).order_by(UserQuizAttempt.attempt_time.desc()).first()
                
                if attempt:
                    quiz_results[quiz.id] = {
                        'score': attempt.score,
                        'passed': attempt.passed,
                        'attempt_time': attempt.attempt_time
                    }
        
        # Get related modules (same procedure or category)
        related_modules = []
        if module.procedure_id:
            related_modules = EducationModule.query.filter(
                EducationModule.procedure_id == module.procedure_id,
                EducationModule.id != module.id
            ).limit(3).all()
        elif module.category_id:
            related_modules = EducationModule.query.filter(
                EducationModule.category_id == module.category_id,
                EducationModule.id != module.id
            ).limit(3).all()
        
        return render_template(
            'education/module.html',
            module=module,
            quizzes=quizzes,
            module_completed=module_completed,
            quiz_results=quiz_results,
            related_modules=related_modules
        )
    except Exception as e:
        logger.error(f"Error viewing education module: {str(e)}")
        return render_template('education/module.html', error=str(e))


@education.route('/quiz/<int:quiz_id>')
def take_quiz(quiz_id):
    """Take a quiz for an education module."""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        module = quiz.module
        questions = quiz.questions.all()
        
        # Check if user has already taken this quiz
        previous_attempt = None
        if current_user.is_authenticated:
            previous_attempt = UserQuizAttempt.query.filter_by(
                user_id=current_user.id,
                quiz_id=quiz.id
            ).order_by(UserQuizAttempt.completed_at.desc()).first()
        
        return render_template(
            'education/quiz.html',
            quiz=quiz,
            module=module,
            questions=questions,
            previous_attempt=previous_attempt
        )
    except Exception as e:
        logger.error(f"Error taking quiz: {str(e)}")
        return render_template('education/quiz.html', error=str(e))


@education.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    """Submit a quiz and see results."""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = quiz.questions.all()
        
        # Process submitted answers
        user_answers = {}
        for question in questions:
            answer_key = f'question_{question.id}'
            if answer_key in request.form:
                user_answers[str(question.id)] = request.form[answer_key]
        
        # Calculate score
        correct_count = 0
        total_questions = len(questions)
        
        for question in questions:
            if str(question.id) in user_answers and user_answers[str(question.id)] == question.correct_answer:
                correct_count += 1
        
        if total_questions > 0:
            score_percentage = round((correct_count / total_questions) * 100)
        else:
            score_percentage = 0
        
        # Check if passed
        passed = score_percentage >= quiz.passing_score
        
        # Save attempt
        attempt = UserQuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz.id,
            score=score_percentage,
            passed=passed,
            answers=user_answers,
            completed_at=datetime.utcnow()
        )
        db.session.add(attempt)
        
        # Add achievement if passed
        if passed:
            achievement = UserAchievement(
                user_id=current_user.id,
                achievement_type='quiz_passed',
                achievement_key=f'quiz_{quiz.id}',
                title=f"Passed: {quiz.title}",
                description=f"Successfully passed {quiz.title} with a score of {score_percentage}%",
                points_awarded=quiz.module.points,
                module_id=quiz.module_id
            )
            db.session.add(achievement)
            
            # Check if all quizzes passed for this module
            all_quizzes = Quiz.query.filter_by(module_id=quiz.module_id).all()
            quiz_ids = [q.id for q in all_quizzes]
            
            # Get passed quizzes
            passed_quizzes = UserQuizAttempt.query.filter(
                UserQuizAttempt.user_id == current_user.id,
                UserQuizAttempt.quiz_id.in_(quiz_ids),
                UserQuizAttempt.passed == True
            ).distinct(UserQuizAttempt.quiz_id).all()
            
            passed_quiz_ids = [attempt.quiz_id for attempt in passed_quizzes]
            
            # If all quizzes passed, add module completion achievement
            if set(quiz_ids).issubset(set(passed_quiz_ids)):
                module_achievement = UserAchievement(
                    user_id=current_user.id,
                    achievement_type='module_completed',
                    achievement_key=f'module_{quiz.module_id}',
                    title=f"Completed: {quiz.module.title}",
                    description=f"Successfully completed the {quiz.module.title} module",
                    points_awarded=quiz.module.points * 2,  # Bonus points for completing the whole module
                    module_id=quiz.module_id
                )
                db.session.add(module_achievement)
        
        db.session.commit()
        
        return redirect(url_for('education.quiz_results', attempt_id=attempt.id))
    except Exception as e:
        logger.error(f"Error submitting quiz: {str(e)}")
        db.session.rollback()
        flash(f"Error submitting quiz: {str(e)}", 'danger')
        return redirect(url_for('education.take_quiz', quiz_id=quiz_id))


@education.route('/quiz/results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    """View quiz results."""
    try:
        attempt = UserQuizAttempt.query.get_or_404(attempt_id)
        
        # Security check - only allow user to see their own results
        if attempt.user_id != current_user.id:
            flash("You don't have permission to view these results.", 'danger')
            return redirect(url_for('education.learn_home'))
        
        quiz = attempt.quiz
        module = quiz.module
        questions = quiz.questions.all()
        
        # Format answers for display
        formatted_answers = []
        for question in questions:
            user_answer = attempt.answers.get(str(question.id), '')
            is_correct = user_answer == question.correct_answer
            
            answer_data = {
                'question': question,
                'user_answer': user_answer,
                'is_correct': is_correct,
                'explanation': question.explanation
            }
            formatted_answers.append(answer_data)
        
        # Check if user has completed this module
        module_completed = UserAchievement.query.filter_by(
            user_id=current_user.id,
            module_id=module.id,
            achievement_type='module_completed'
        ).first() is not None
        
        return render_template(
            'education/quiz_results.html',
            attempt=attempt,
            quiz=quiz,
            module=module,
            formatted_answers=formatted_answers,
            module_completed=module_completed
        )
    except Exception as e:
        logger.error(f"Error viewing quiz results: {str(e)}")
        flash(f"Error viewing quiz results: {str(e)}", 'danger')
        return redirect(url_for('education.learn_home'))


@education.route('/achievements')
@login_required
def view_achievements():
    """View user achievements."""
    try:
        # Get all user achievements
        achievements = UserAchievement.query.filter_by(user_id=current_user.id).order_by(UserAchievement.earned_at.desc()).all()
        
        # Group achievements by type
        modules_completed = [ach for ach in achievements if ach.achievement_type == 'module_completed']
        quizzes_passed = [ach for ach in achievements if ach.achievement_type == 'quiz_passed']
        
        # Calculate statistics
        total_modules = EducationModule.query.count()
        completed_count = len(modules_completed)
        completion_percentage = round((completed_count / total_modules) * 100) if total_modules > 0 else 0
        
        # Get user's level based on achievements
        user_level = (completed_count // 5) + 1  # Level up every 5 completed modules
        
        return render_template(
            'education/achievements.html',
            achievements=achievements,
            modules_completed=modules_completed,
            quizzes_passed=quizzes_passed,
            total_modules=total_modules,
            completed_count=completed_count,
            completion_percentage=completion_percentage,
            user_level=user_level
        )
    except Exception as e:
        logger.error(f"Error viewing achievements: {str(e)}")
        flash(f"Error viewing achievements: {str(e)}", 'danger')
        return redirect(url_for('education.learn_home'))