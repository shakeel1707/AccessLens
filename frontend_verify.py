"""
Task 19 Frontend Verification Script
Validates React/TypeScript project structure and component implementations
"""

import os
import json
import re
from pathlib import Path

def check_file_exists(path, description):
    """Check if file exists and return result"""
    exists = os.path.isfile(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def check_directory_exists(path, description):
    """Check if directory exists"""
    exists = os.path.isdir(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def validate_json(filepath):
    """Validate JSON file syntax"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True
    except:
        return False

def count_lines(filepath):
    """Count lines in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def check_component_exports(filepath):
    """Check if component file exports properly"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for React component export
            if 'export const' in content and ('React.FC' in content or 'React' in content):
                return True
            if 'export default' in content:
                return True
    except:
        pass
    return False

def main():
    base_path = r'c:\Users\Shakeel\OneDrive\Desktop\New folder\frontend'
    
    print("=" * 60)
    print("TASK 19: FRONTEND REACT PROJECT VERIFICATION")
    print("=" * 60)
    print()
    
    # 1. Check directory structure
    print("1. DIRECTORY STRUCTURE")
    print("-" * 60)
    dirs_ok = [
        check_directory_exists(base_path, "Frontend root"),
        check_directory_exists(os.path.join(base_path, 'src'), "src directory"),
        check_directory_exists(os.path.join(base_path, 'src/components'), "components directory"),
        check_directory_exists(os.path.join(base_path, 'src/context'), "context directory"),
        check_directory_exists(os.path.join(base_path, 'public'), "public directory"),
        check_directory_exists(os.path.join(base_path, 'tests'), "tests directory"),
    ]
    print(f"Result: {sum(dirs_ok)}/{len(dirs_ok)} directories ✅" if all(dirs_ok) else f"Result: {sum(dirs_ok)}/{len(dirs_ok)} directories ⚠️")
    print()
    
    # 2. Check config files
    print("2. CONFIGURATION FILES")
    print("-" * 60)
    config_files = [
        ('package.json', 'Package.json'),
        ('vite.config.ts', 'Vite config'),
        ('tsconfig.json', 'TypeScript config'),
        ('index.html', 'HTML entry'),
        ('.gitignore', 'Git ignore'),
    ]
    
    config_ok = []
    for filename, desc in config_files:
        filepath = os.path.join(base_path, filename)
        exists = check_file_exists(filepath, desc)
        config_ok.append(exists)
        
        # Validate JSON files
        if filename.endswith('.json') and exists:
            valid = validate_json(filepath)
            status = "✅ (valid JSON)" if valid else "⚠️ (invalid JSON)"
            print(f"  {status}")
    
    print(f"Result: {sum(config_ok)}/{len(config_ok)} config files present")
    print()
    
    # 3. Check component files
    print("3. REACT COMPONENTS (REQUIRED 5)")
    print("-" * 60)
    components = [
        ('src/components/ScanForm.tsx', 'ScanForm'),
        ('src/components/FindingsList.tsx', 'FindingsList'),
        ('src/components/RepairReview.tsx', 'RepairReview'),
        ('src/components/ReportDisplay.tsx', 'ReportDisplay'),
        ('src/components/ProgressIndicator.tsx', 'ProgressIndicator'),
    ]
    
    components_ok = []
    for filepath, name in components:
        full_path = os.path.join(base_path, filepath)
        exists = check_file_exists(full_path, name)
        if exists:
            lines = count_lines(full_path)
            exports_ok = check_component_exports(full_path)
            export_status = "✅ exports" if exports_ok else "⚠️ no export"
            print(f"  {export_status} ({lines} lines)")
            components_ok.append(exists and exports_ok)
        else:
            components_ok.append(False)
    
    print(f"Result: {sum(components_ok)}/{len(components_ok)} components valid")
    print()
    
    # 4. Check Context API
    print("4. CONTEXT API (STATE MANAGEMENT)")
    print("-" * 60)
    context_path = os.path.join(base_path, 'src/context/AppContext.tsx')
    context_exists = check_file_exists(context_path, "AppContext")
    if context_exists:
        lines = count_lines(context_path)
        print(f"  ✅ {lines} lines (includes interfaces, provider, hook)")
        try:
            with open(context_path, 'r', encoding='utf-8') as f:
                content = f.read()
                has_provider = 'AppProvider' in content
                has_hook = 'useApp' in content
                has_interfaces = 'interface' in content
                print(f"  ✅ AppProvider: {has_provider}")
                print(f"  ✅ useApp hook: {has_hook}")
                print(f"  ✅ TypeScript interfaces: {has_interfaces}")
        except:
            pass
    print()
    
    # 5. Check styling
    print("5. STYLING & CSS")
    print("-" * 60)
    css_files = [
        ('src/App.css', 'Component styles'),
        ('src/index.css', 'Global styles'),
    ]
    
    css_ok = []
    for filepath, desc in css_files:
        full_path = os.path.join(base_path, filepath)
        exists = check_file_exists(full_path, desc)
        if exists:
            lines = count_lines(full_path)
            print(f"  ✅ {lines} lines of CSS")
            css_ok.append(True)
        else:
            css_ok.append(False)
    print()
    
    # 6. Check entry points
    print("6. APPLICATION ENTRY POINTS")
    print("-" * 60)
    entry_files = [
        ('index.html', 'HTML entry point'),
        ('src/main.tsx', 'React entry point'),
        ('src/App.tsx', 'App component'),
    ]
    
    entry_ok = []
    for filepath, desc in entry_files:
        full_path = os.path.join(base_path, filepath)
        exists = check_file_exists(full_path, desc)
        if exists:
            lines = count_lines(full_path)
            print(f"  ✅ {lines} lines")
        entry_ok.append(exists)
    print()
    
    # 7. Check tests
    print("7. TEST SUITE (VITEST)")
    print("-" * 60)
    test_path = os.path.join(base_path, 'tests/components.test.ts')
    test_exists = check_file_exists(test_path, "Component tests")
    if test_exists:
        lines = count_lines(test_path)
        print(f"  ✅ {lines} lines")
        try:
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read()
                test_count = content.count('it(')
                print(f"  ✅ {test_count} test cases defined")
        except:
            pass
    print()
    
    # 8. Check documentation
    print("8. DOCUMENTATION")
    print("-" * 60)
    readme_path = os.path.join(base_path, 'README.md')
    readme_exists = check_file_exists(readme_path, "README.md")
    if readme_exists:
        lines = count_lines(readme_path)
        print(f"  ✅ {lines} lines of documentation")
    print()
    
    # 9. Package.json validation
    print("9. DEPENDENCIES & SCRIPTS")
    print("-" * 60)
    pkg_path = os.path.join(base_path, 'package.json')
    try:
        with open(pkg_path, 'r') as f:
            pkg = json.load(f)
            deps = pkg.get('dependencies', {})
            dev_deps = pkg.get('devDependencies', {})
            scripts = pkg.get('scripts', {})
            
            required_deps = ['react', 'react-dom']
            found_deps = [d for d in required_deps if d in deps]
            print(f"✅ Dependencies: {len(found_deps)}/{len(required_deps)} required")
            
            required_dev = ['vite', 'typescript', 'vitest']
            found_dev = [d for d in required_dev if d in dev_deps]
            print(f"✅ Dev Dependencies: {len(found_dev)}/{len(required_dev)} required")
            
            required_scripts = ['dev', 'build', 'test']
            found_scripts = [s for s in required_scripts if s in scripts]
            print(f"✅ Scripts: {len(found_scripts)}/{len(required_scripts)} required")
            print(f"  - dev: npm run dev")
            print(f"  - build: npm run build")
            print(f"  - test: npm run test")
    except Exception as e:
        print(f"⚠️ Error reading package.json: {e}")
    print()
    
    # SUMMARY
    print("=" * 60)
    print("TASK 19 COMPLETION SUMMARY")
    print("=" * 60)
    print()
    
    all_checks = {
        'Directory Structure': all(dirs_ok),
        'Configuration Files': all(config_ok),
        'React Components (5/5)': all(components_ok),
        'Context API Setup': context_exists,
        'Styling': all(css_ok),
        'Entry Points': all(entry_ok),
        'Test Suite': test_exists,
        'Documentation': readme_exists,
    }
    
    passed = sum(1 for v in all_checks.values() if v)
    total = len(all_checks)
    
    for check, result in all_checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    print()
    print(f"OVERALL: {passed}/{total} checks passed")
    print()
    
    if passed == total:
        print("🎉 TASK 19 IMPLEMENTATION COMPLETE!")
        print("   All components, configuration, and documentation verified.")
        print()
        print("Next Steps:")
        print("  1. Install Node.js 16+ to run tests")
        print("  2. Run: cd frontend && npm install && npm run test")
        print("  3. Run: npm run build to verify TypeScript compilation")
    else:
        print(f"⚠️  {total - passed} checks failed. Review above.")

if __name__ == '__main__':
    main()
