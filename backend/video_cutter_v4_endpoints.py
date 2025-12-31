# Additional API endpoints for VideoCutter V4
# Add these to video_cutter.py

# === ADD THESE IMPORTS ===
# import shutil

# === ADD THESE ENDPOINTS ===

@cutter_bp.route('/folder-files/<folder_name>', methods=['GET'])
def get_folder_files(folder_name):
    """Get list of files in a folder"""
    try:
        # Check both cuts and archive directories
        folder_path = os.path.join(CUTS_DIR, folder_name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        files = []
        for f in sorted(os.listdir(folder_path)):
            if f.endswith('.mp4'):
                file_path = os.path.join(folder_path, f)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                files.append({
                    'filename': f,
                    'size_mb': round(size_mb, 2),
                    'download_url': f'/video-outputs/cuts/{folder_name}/{f}',
                    's3_url': f'{S3_PUBLIC_URL}/outputs/cuts/{folder_name}/{f}' if S3_PUBLIC_URL else None
                })
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'files': files,
            'total': len(files)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/rename-folder', methods=['POST'])
def rename_folder():
    """Rename a folder"""
    try:
        data = request.get_json()
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        
        if not old_name or not new_name:
            return jsonify({'success': False, 'error': 'old_name and new_name required'})
        
        # Sanitize new name
        new_name = re.sub(r'[^a-zA-Z0-9_-]', '_', new_name)
        
        # Check both directories
        old_path = os.path.join(CUTS_DIR, old_name)
        is_archived = False
        if not os.path.exists(old_path):
            old_path = os.path.join(ARCHIVE_DIR, old_name)
            is_archived = True
        
        if not os.path.exists(old_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        base_dir = ARCHIVE_DIR if is_archived else CUTS_DIR
        new_path = os.path.join(base_dir, new_name)
        
        if os.path.exists(new_path):
            return jsonify({'success': False, 'error': 'Folder with this name already exists'})
        
        os.rename(old_path, new_path)
        
        return jsonify({
            'success': True,
            'old_name': old_name,
            'new_name': new_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/archive-folder/<folder_name>', methods=['POST'])
def archive_folder(folder_name):
    """Move folder to archive"""
    try:
        src_path = os.path.join(CUTS_DIR, folder_name)
        dst_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(src_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        if os.path.exists(dst_path):
            return jsonify({'success': False, 'error': 'Folder already in archive'})
        
        shutil.move(src_path, dst_path)
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'archived': True
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/unarchive-folder/<folder_name>', methods=['POST'])
def unarchive_folder(folder_name):
    """Restore folder from archive"""
    try:
        src_path = os.path.join(ARCHIVE_DIR, folder_name)
        dst_path = os.path.join(CUTS_DIR, folder_name)
        
        if not os.path.exists(src_path):
            return jsonify({'success': False, 'error': 'Folder not found in archive'})
        
        if os.path.exists(dst_path):
            return jsonify({'success': False, 'error': 'Folder already exists in cuts'})
        
        shutil.move(src_path, dst_path)
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'archived': False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/delete-files', methods=['POST'])
def delete_files():
    """Delete specific files from folder"""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name')
        filenames = data.get('filenames', [])
        
        if not folder_name or not filenames:
            return jsonify({'success': False, 'error': 'folder_name and filenames required'})
        
        # Check both directories
        folder_path = os.path.join(CUTS_DIR, folder_name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        deleted = []
        errors = []
        
        for filename in filenames:
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted.append(filename)
                except Exception as e:
                    errors.append({'filename': filename, 'error': str(e)})
            else:
                errors.append({'filename': filename, 'error': 'File not found'})
        
        return jsonify({
            'success': True,
            'deleted': deleted,
            'deleted_count': len(deleted),
            'errors': errors if errors else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/s3-urls/<folder_name>', methods=['GET'])
def get_s3_urls(folder_name):
    """Get S3 URLs for all files in folder"""
    try:
        # Check both directories
        folder_path = os.path.join(CUTS_DIR, folder_name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        urls = []
        for f in sorted(os.listdir(folder_path)):
            if f.endswith('.mp4'):
                urls.append({
                    'filename': f,
                    's3_url': f'{S3_PUBLIC_URL}/outputs/cuts/{folder_name}/{f}' if S3_PUBLIC_URL else None,
                    'download_url': f'/video-outputs/cuts/{folder_name}/{f}'
                })
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'urls': urls,
            'total': len(urls)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# === UPDATE folders endpoint to show archived status ===
@cutter_bp.route('/folders', methods=['GET'])
def list_folders():
    """List all cut folders (active and archived)"""
    folders = []
    
    # Active folders
    if os.path.exists(CUTS_DIR):
        for name in os.listdir(CUTS_DIR):
            path = os.path.join(CUTS_DIR, name)
            if os.path.isdir(path):
                files = [f for f in os.listdir(path) if f.endswith('.mp4')]
                total_size = sum(os.path.getsize(os.path.join(path, f)) for f in files) / (1024*1024)
                folders.append({
                    'name': name,
                    'path': path,
                    'files_count': len(files),
                    'total_size_mb': round(total_size, 1),
                    'created': datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
                    'archived': False
                })
    
    # Archived folders
    if os.path.exists(ARCHIVE_DIR):
        for name in os.listdir(ARCHIVE_DIR):
            path = os.path.join(ARCHIVE_DIR, name)
            if os.path.isdir(path):
                files = [f for f in os.listdir(path) if f.endswith('.mp4')]
                total_size = sum(os.path.getsize(os.path.join(path, f)) for f in files) / (1024*1024)
                folders.append({
                    'name': name,
                    'path': path,
                    'files_count': len(files),
                    'total_size_mb': round(total_size, 1),
                    'created': datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
                    'archived': True
                })
    
    folders.sort(key=lambda x: x['created'], reverse=True)
    
    return jsonify({
        'success': True,
        'folders': folders,
        'total': len(folders)
    })
