"""
Reddit Import System - Import posts from Reddit to community platform
"""

import requests
import json
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models import Community, RedditImport, User, Category, Procedure
import logging

logger = logging.getLogger(__name__)

# Create blueprint
reddit_import_bp = Blueprint('reddit_import', __name__, url_prefix='/admin/reddit')

class RedditImporter:
    """Handle Reddit post importing functionality."""
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
    
    def extract_post_id(self, reddit_url):
        """Extract Reddit post ID from URL."""
        # Handle various Reddit URL formats
        patterns = [
            r'reddit\.com/r/\w+/comments/([a-z0-9]+)',
            r'redd\.it/([a-z0-9]+)',
            r'/comments/([a-z0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, reddit_url)
            if match:
                return match.group(1)
        
        return None
    
    def fetch_reddit_post(self, reddit_url):
        """Fetch post data from Reddit API."""
        try:
            # Extract post ID
            post_id = self.extract_post_id(reddit_url)
            if not post_id:
                return None, "Invalid Reddit URL format"
            
            # Construct API URL
            api_url = f"{reddit_url}.json"
            if not api_url.startswith('http'):
                api_url = f"https://www.reddit.com{reddit_url}.json"
            
            # Add .json if not present
            if not api_url.endswith('.json'):
                api_url += '.json'
            
            # Fetch data
            headers = {
                'User-Agent': 'Antidote Medical Community Bot 1.0'
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract post data
            if isinstance(data, list) and len(data) > 0:
                post_data = data[0]['data']['children'][0]['data']
                comments_data = data[1]['data']['children'] if len(data) > 1 else []
                
                return {
                    'post': post_data,
                    'comments': comments_data
                }, None
            
            return None, "Unable to parse Reddit response"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Reddit post: {str(e)}")
            return None, f"Failed to fetch Reddit post: {str(e)}"
        except Exception as e:
            logger.error(f"Error processing Reddit data: {str(e)}")
            return None, f"Error processing Reddit data: {str(e)}"
    
    def import_post_to_community(self, reddit_data, admin_user_id, category_id=None, procedure_id=None):
        """Import Reddit post data to community table."""
        try:
            post_data = reddit_data['post']
            
            # Extract media URLs
            media_urls = []
            if post_data.get('url') and any(ext in post_data['url'] for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                media_urls.append(post_data['url'])
            
            # Handle Reddit gallery
            if post_data.get('media_metadata'):
                for media_id, media_info in post_data['media_metadata'].items():
                    if media_info.get('s', {}).get('u'):
                        media_urls.append(media_info['s']['u'].replace('&amp;', '&'))
            
            # Create community post
            community_post = Community(
                user_id=admin_user_id,  # Assign to admin who imported
                title=post_data['title'],
                content=post_data.get('selftext', '') or f"Original post: {post_data.get('url', '')}",
                source_type='reddit',
                source_url=f"https://www.reddit.com{post_data['permalink']}",
                reddit_id=post_data['id'],
                reddit_author=post_data['author'],
                imported_at=datetime.utcnow(),
                imported_by_admin=admin_user_id,
                upvotes=max(0, post_data.get('ups', 0)),
                downvotes=max(0, post_data.get('downs', 0)),
                view_count=0,
                reply_count=post_data.get('num_comments', 0),
                media_urls=media_urls,
                source_metadata={
                    'subreddit': post_data.get('subreddit'),
                    'original_created_utc': post_data.get('created_utc'),
                    'score': post_data.get('score', 0),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'gildings': post_data.get('gildings', {}),
                    'awards': post_data.get('all_awardings', [])
                },
                category_id=category_id,
                procedure_id=procedure_id,
                is_anonymous=True,  # Reddit posts are imported as anonymous
                created_at=datetime.fromtimestamp(post_data.get('created_utc', 0)) if post_data.get('created_utc') else datetime.utcnow()
            )
            
            # Calculate initial engagement score
            community_post.total_votes = (community_post.upvotes or 0) - (community_post.downvotes or 0)
            community_post.engagement_score = self.calculate_engagement_score(community_post)
            
            db.session.add(community_post)
            db.session.flush()  # Get the ID
            
            return community_post, None
            
        except Exception as e:
            logger.error(f"Error importing post to community: {str(e)}")
            return None, f"Failed to import post: {str(e)}"
    
    def calculate_engagement_score(self, post):
        """Calculate engagement score for imported posts."""
        upvotes = post.upvotes or 0
        downvotes = post.downvotes or 0
        comments = post.reply_count or 0
        
        # Basic scoring for imported content
        score = upvotes - downvotes + (comments * 0.5)
        
        # Reduce score for imported content to prioritize native content
        return max(0, score * 0.7)

# Initialize importer
reddit_importer = RedditImporter()

@reddit_import_bp.route('/')
@login_required
def import_dashboard():
    """Admin dashboard for Reddit imports."""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('web.index'))
    
    # Get recent imports
    recent_imports = RedditImport.query.order_by(
        RedditImport.import_date.desc()
    ).limit(20).all()
    
    # Get categories and procedures for selection
    categories = Category.query.all()
    procedures = Procedure.query.all()
    
    return render_template('admin/reddit_import.html', 
                         recent_imports=recent_imports,
                         categories=categories,
                         procedures=procedures)

@reddit_import_bp.route('/import', methods=['POST'])
@login_required
def import_reddit_post():
    """Import a single Reddit post."""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        reddit_url = data.get('reddit_url', '').strip()
        category_id = data.get('category_id')
        procedure_id = data.get('procedure_id')
        
        if not reddit_url:
            return jsonify({'success': False, 'message': 'Reddit URL is required'}), 400
        
        # Check if already imported
        existing_import = RedditImport.query.filter_by(reddit_url=reddit_url).first()
        if existing_import:
            return jsonify({
                'success': False, 
                'message': 'This Reddit post has already been imported'
            }), 400
        
        # Create import record
        import_record = RedditImport(
            reddit_url=reddit_url,
            reddit_post_id='',  # Will be filled after extraction
            import_status='pending',
            imported_by_admin=current_user.id
        )
        db.session.add(import_record)
        db.session.flush()
        
        # Fetch Reddit data
        reddit_data, error = reddit_importer.fetch_reddit_post(reddit_url)
        if error:
            import_record.import_status = 'failed'
            import_record.error_message = error
            db.session.commit()
            return jsonify({'success': False, 'message': error}), 400
        
        # Update import record with post ID
        import_record.reddit_post_id = reddit_data['post']['id']
        import_record.original_post_data = reddit_data
        
        # Import to community
        community_post, error = reddit_importer.import_post_to_community(
            reddit_data, current_user.id, category_id, procedure_id
        )
        
        if error:
            import_record.import_status = 'failed'
            import_record.error_message = error
            db.session.commit()
            return jsonify({'success': False, 'message': error}), 500
        
        # Update import record
        import_record.import_status = 'completed'
        import_record.community_id = community_post.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reddit post imported successfully',
            'community_post_id': community_post.id,
            'post_title': community_post.title
        })
        
    except Exception as e:
        logger.error(f"Error importing Reddit post: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Import failed: {str(e)}'
        }), 500

@reddit_import_bp.route('/bulk-import', methods=['POST'])
@login_required
def bulk_import_reddit_posts():
    """Import multiple Reddit posts from a list of URLs."""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        reddit_urls = data.get('reddit_urls', [])
        category_id = data.get('category_id')
        procedure_id = data.get('procedure_id')
        
        if not reddit_urls or not isinstance(reddit_urls, list):
            return jsonify({'success': False, 'message': 'Valid URL list is required'}), 400
        
        results = []
        successful_imports = 0
        failed_imports = 0
        
        for url in reddit_urls:
            url = url.strip()
            if not url:
                continue
                
            try:
                # Check if already imported
                existing_import = RedditImport.query.filter_by(reddit_url=url).first()
                if existing_import:
                    results.append({
                        'url': url,
                        'status': 'skipped',
                        'message': 'Already imported'
                    })
                    continue
                
                # Create import record
                import_record = RedditImport(
                    reddit_url=url,
                    reddit_post_id='',
                    import_status='pending',
                    imported_by_admin=current_user.id
                )
                db.session.add(import_record)
                db.session.flush()
                
                # Fetch and import
                reddit_data, error = reddit_importer.fetch_reddit_post(url)
                if error:
                    import_record.import_status = 'failed'
                    import_record.error_message = error
                    results.append({
                        'url': url,
                        'status': 'failed',
                        'message': error
                    })
                    failed_imports += 1
                    continue
                
                # Import to community
                community_post, error = reddit_importer.import_post_to_community(
                    reddit_data, current_user.id, category_id, procedure_id
                )
                
                if error:
                    import_record.import_status = 'failed'
                    import_record.error_message = error
                    results.append({
                        'url': url,
                        'status': 'failed',
                        'message': error
                    })
                    failed_imports += 1
                    continue
                
                # Success
                import_record.reddit_post_id = reddit_data['post']['id']
                import_record.original_post_data = reddit_data
                import_record.import_status = 'completed'
                import_record.community_id = community_post.id
                
                results.append({
                    'url': url,
                    'status': 'success',
                    'message': f'Imported: {community_post.title}',
                    'community_post_id': community_post.id
                })
                successful_imports += 1
                
            except Exception as e:
                logger.error(f"Error importing URL {url}: {str(e)}")
                results.append({
                    'url': url,
                    'status': 'failed',
                    'message': str(e)
                })
                failed_imports += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Bulk import completed: {successful_imports} successful, {failed_imports} failed',
            'results': results,
            'summary': {
                'successful': successful_imports,
                'failed': failed_imports,
                'total': len(reddit_urls)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in bulk import: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Bulk import failed: {str(e)}'
        }), 500

@reddit_import_bp.route('/preview', methods=['POST'])
@login_required
def preview_reddit_post():
    """Preview Reddit post before importing."""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        reddit_url = data.get('reddit_url', '').strip()
        
        if not reddit_url:
            return jsonify({'success': False, 'message': 'Reddit URL is required'}), 400
        
        # Fetch Reddit data
        reddit_data, error = reddit_importer.fetch_reddit_post(reddit_url)
        if error:
            return jsonify({'success': False, 'message': error}), 400
        
        post_data = reddit_data['post']
        
        # Return preview data
        preview = {
            'title': post_data['title'],
            'content': post_data.get('selftext', ''),
            'author': post_data['author'],
            'subreddit': post_data.get('subreddit'),
            'score': post_data.get('score', 0),
            'upvote_ratio': post_data.get('upvote_ratio', 0),
            'num_comments': post_data.get('num_comments', 0),
            'created_utc': post_data.get('created_utc'),
            'url': post_data.get('url'),
            'media_urls': []
        }
        
        # Extract media URLs for preview
        if post_data.get('url') and any(ext in post_data['url'] for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            preview['media_urls'].append(post_data['url'])
        
        return jsonify({
            'success': True,
            'preview': preview
        })
        
    except Exception as e:
        logger.error(f"Error previewing Reddit post: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Preview failed: {str(e)}'
        }), 500

# Register the blueprint
def register_reddit_import(app):
    """Register Reddit import routes."""
    app.register_blueprint(reddit_import_bp)