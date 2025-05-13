import os
import glob
import platform

def generate_pyinstaller_command(main_script='main.py'):
    # Get the current project directory
    project_dir = os.getcwd()

    # Get the full path of the main script
    main_script_path = os.path.join(project_dir, main_script)
    if not os.path.exists(main_script_path):
        print(f"Error: Main script '{main_script}' not found at '{main_script_path}'.")
        return

    # Check for the icon file
    icon_file = os.path.join(project_dir, 'ppg.ico')
    if not os.path.exists(icon_file):
        print(f"Error: Icon file 'ppg.ico' not found at '{icon_file}'.")
        return

    # Define file extensions to include (excluding the icon file)
    extensions = ['*.mp3', '*.png', '*.json']

    # Collect files in the root directory
    files_to_include = []
    for ext in extensions:
        files_to_include.extend(glob.glob(os.path.join(project_dir, ext)))

    # Collect HTML files in the templates directory
    templates_dir = os.path.join(project_dir, 'templates')
    if os.path.exists(templates_dir):
        html_files = glob.glob(os.path.join(templates_dir, '*.html'))
        files_to_include.extend(html_files)

    # Start building the PyInstaller command
    command = [
        'pyinstaller', '--noconsole', '--onefile', '--uac-admin', '--name "xagent_optimiser_v1.0.1"', f'--icon "{icon_file}"']

    # Use colon as separator for --add-data on Windows
    separator = ':'

    # Add each file to the command with --add-data
    for file_path in files_to_include:
        # Determine the destination path in the executable
        rel_path = os.path.relpath(file_path, project_dir)
        dest_dir = os.path.dirname(rel_path) if os.path.dirname(rel_path) else '.'
        command.append(f'--add-data "{file_path}{separator}{dest_dir}"')

    # Add the main script to the command
    command.append(f'"{main_script_path}"')

    # Join the command parts
    final_command = ' '.join(command)

    # print the command
    print("\nGenerated PyInstaller command:")
    print(final_command)
    print("\nCopy and run the above command in your terminal, or use the generated 'build.bat' file.")

    # Save the command to a batch file for easy execution
    batch_file_path = os.path.join(project_dir, 'build.bat')
    with open(batch_file_path, 'w') as batch_file:
        batch_file.write('@echo off\n')
        batch_file.write(final_command + '\n')
        batch_file.write('pause\n')

    print(f"\nBatch file created at: {batch_file_path}")
    print("Run 'build.bat' in the project folder to execute the PyInstaller command.")

if __name__ == '__main__':
    generate_pyinstaller_command(main_script='main.py')
