#!/usr/bin/env python3
"""
Script to find and copy the legal_support_agents.py module to the root directory
for easier importing in Azure App Service.
"""

import os
import glob
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Find and copy the legal_support_agents.py file to the root directory."""
    logger.info("Searching for legal_support_agents.py file...")
    
    # Search for the file
    crew_files = glob.glob("src/**/legal_support_agents.py", recursive=True)
    
    if not crew_files:
        logger.error("Could not find legal_support_agents.py in the src directory")
        return False
    
    # Get the first match
    source_file = crew_files[0]
    logger.info(f"Found file at: {source_file}")
    
    # Copy to root
    try:
        shutil.copy(source_file, "legal_support_agents_module.py")
        logger.info("Successfully copied to legal_support_agents_module.py in the root directory")
        
        # If the file includes the class definition, we should be able to import it directly
        with open("legal_support_agents_module.py", "r") as f:
            content = f.read()
            if "class LegalSupportCrew" in content:
                logger.info("Verified that LegalSupportCrew class exists in the copied file")
            else:
                logger.warning("LegalSupportCrew class may not be in the copied file")
        
        return True
    except Exception as e:
        logger.error(f"Error copying file: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("Setup completed successfully")
    else:
        print("Setup failed")
        exit(1) 