from flask import render_template, request,url_for,Blueprint,jsonify
from flask_login import login_required
from flask_login import current_user,login_required
from apps.authentication.models import Dataset,Users,db,Notification 
from jinja2 import TemplateNotFound
from apps.dataset_search.dataset import search_kaggle_datasets,get_dataset_metadata,datasets
from apps.home import blueprint
from apps import db

# Modify the existing routes to include dataset search functionality
@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500

# New route for dataset search
@blueprint.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_term = request.form['search']

        # Search local (mock) datasets
        local_filtered_datasets = [dataset for dataset in datasets if search_term.lower() in dataset['source_name'].lower()]  # Modified comparison logic

        # Search Kaggle datasets
        kaggle_datasets = search_kaggle_datasets(search_term)  # Modified search term

        # Combine results from all sources
        all_datasets = local_filtered_datasets + kaggle_datasets
        total_results = len(all_datasets)

        if not all_datasets:
            print("No search results found for", search_term)
            return render_template('search_results.html', datasets=[], message="No datasets found matching your search term.")

        return render_template('search_results.html', total_results=total_results,datasets=all_datasets)
    else:
        # Handle GET request (render search form)
        return render_template('search.html')
    
@blueprint.route('/save_dataset', methods=['POST'])
@login_required
def save_dataset():
    try:
        data = request.json
        dataset_name = data['dataset_name']
        dataset_link = data['dataset_link']

        # Create a new Dataset object and add it to the database session
        new_dataset = Dataset(dataset_name=dataset_name, dataset_link=dataset_link, user_id=current_user.id)
        db.session.add(new_dataset)
        db.session.commit()
        # Create a notification
        notification = Notification(message='Dataset saved successfully', user_id=current_user.id)
        db.session.add(notification)
        db.session.commit()

        return jsonify({'message': 'Dataset saved successfully'}), 200
    except KeyError:
        return jsonify({'error': 'Missing dataset information'}), 400
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    

@blueprint.route('/remove_dataset', methods=['POST'])
@login_required   
def remove_dataset():
    if request.method == 'POST':
        # Get the dataset ID from the request
        dataset_id = request.json.get('dataset_id')

        # Find the dataset in the database
        dataset = Dataset.query.get(dataset_id)

        if dataset:
            # Check if the dataset belongs to the current user
            if dataset.user_id == current_user.id:
                # Remove the dataset from the database
                db.session.delete(dataset)
                db.session.commit()
                notification = Notification(message='Dataset removed successfully', user_id=current_user.id)
                db.session.add(notification)
                db.session.commit()
                return jsonify({'message': 'Dataset removed successfully'}), 200
            else:
                return jsonify({'error': 'Unauthorized access to remove dataset'}), 403
        else:
            return jsonify({'error': 'Dataset not found'}), 404
    else:
        return jsonify({'error': 'Method not allowed'}), 405


@blueprint.route('/pinned_datasets')
def pinned_datasets():
    
    saved_datasets = Dataset.query.all()
    print(saved_datasets)
    return render_template('pinned_datasets.html', datasets=saved_datasets)

@blueprint.route('/notifications')
@login_required
def notifications():
    # Retrieve notifications for the current user
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', notifications=user_notifications)

def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
