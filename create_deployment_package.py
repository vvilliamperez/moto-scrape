import os
import subprocess
import glob


def run_command(command):
    """Helper function to run shell commands."""
    result = subprocess.run(command, shell=True, check=True)
    return result


def read_requirements_file(requirements_file):
    """Reads the requirements.txt file and returns a list of packages."""
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as file:
            packages = [line.strip() for line in file if line.strip()]
            return packages
    else:
        print(f"Error: {requirements_file} not found.")
        return []


def find_python_files(project_dir):
    """Finds all Python files in the project directory."""
    return glob.glob(os.path.join(project_dir, "*.py"))


def create_deployment_package(project_dir):
    project_dir = os.path.abspath(project_dir)
    requirements_file = os.path.join(project_dir, "requirements.txt")

    if not os.path.exists(project_dir):
        print(f"Project directory '{project_dir}' not found!")
        return

    # Step 1: Navigate to the project directory
    os.chdir(project_dir)
    print(f"Changed directory to: {project_dir}")

    # Step 2: Create package directory
    package_dir = os.path.join(project_dir, "package")
    os.makedirs(package_dir, exist_ok=True)
    print(f"Created package directory at: {package_dir}")

    # Step 3: Read the requirements file and install the packages
    requirements_file = os.path.join(project_dir, requirements_file)
    packages = read_requirements_file(requirements_file)
    if not packages:
        print("Error: No packages found in the requirements file.")
        return

    try:
        for package in packages:
            print(f"Installing {package} into package directory...")
            run_command(f"pip install --target {package_dir} {package}")
        print("Installed all packages into package directory.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to install dependencies. {e}")
        return

    # Step 4: Zip the dependencies
    os.chdir(package_dir)
    try:
        run_command("zip -r ../my_deployment_package.zip .")
        print("Zipped dependencies into my_deployment_package.zip")
    except subprocess.CalledProcessError:
        print("Error: Failed to zip the dependencies.")
        return

    # Step 5: Find and add all Python files to the zip file
    os.chdir(project_dir)
    python_files = find_python_files(project_dir)
    if not python_files:
        print("Error: No Python files found in the project directory.")
        return

    try:
        for py_file in python_files:
            print(f"Adding {py_file} to my_deployment_package.zip")
            run_command(f"zip my_deployment_package.zip {py_file}")
        print("Added all Python files to my_deployment_package.zip")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to add Python files to the zip package. {e}")
        return

    print("Deployment package created successfully!")


if __name__ == "__main__":
    project_dir = "scrapeAf1"  # Hardcoded directory name
    create_deployment_package(project_dir)
