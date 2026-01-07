import streamlit as st
import subprocess
import os
import sys
from pathlib import Path
import threading
import queue
import time

st.set_page_config(page_title="Real Linux Terminal", layout="wide")

# SECURITY WARNING: This is DANGEROUS in production!
# Only run on trusted, isolated systems.

st.title("🔐 Real Linux Terminal in Streamlit")
st.warning("⚠️ **SECURITY WARNING**: This executes REAL Linux commands. Use only in trusted, isolated environments!")

# Initialize session state
if 'command_history' not in st.session_state:
    st.session_state.command_history = []
if 'current_dir' not in st.session_state:
    st.session_state.current_dir = os.getcwd()
if 'output_buffer' not in st.session_state:
    st.session_state.output_buffer = ""

def execute_command(command, timeout=30):
    """Execute real Linux command with timeout"""
    try:
        # Change directory if needed
        if command.startswith("cd "):
            new_dir = command[3:].strip()
            if new_dir == "~":
                new_dir = os.path.expanduser("~")
            elif not os.path.isabs(new_dir):
                new_dir = os.path.join(st.session_state.current_dir, new_dir)
            
            if os.path.isdir(new_dir):
                os.chdir(new_dir)
                st.session_state.current_dir = os.getcwd()
                return f"Changed directory to: {st.session_state.current_dir}"
            else:
                return f"cd: {new_dir}: No such directory"
        
        # Execute command
        if command.strip() == "pwd":
            return st.session_state.current_dir
        elif command.strip() == "ls":
            # Use python to list files
            files = os.listdir(st.session_state.current_dir)
            return "  ".join(files)
        
        # Run actual shell command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=st.session_state.current_dir
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nError: {result.stderr}"
        
        return output.strip()
    
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {str(e)}"

# Safe command list (for demo)
SAFE_COMMANDS = ["ls", "pwd", "echo", "cat", "whoami", "hostname", 
                 "date", "ps", "df", "free", "uptime", "uname -a"]

# Create UI
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Terminal")
    
    # Display command history
    for cmd, output in st.session_state.command_history[-20:]:
        st.code(f"$ {cmd}", language="bash")
        if output:
            st.text(output)
    
    # Command input
    command = st.text_input(
        "Enter Linux command:",
        key="cmd_input",
        placeholder="Type a command (ls, pwd, etc.)"
    )
    
    if st.button("Execute", type="primary"):
        if command:
            # Execute command
            output = execute_command(command)
            
            # Add to history
            st.session_state.command_history.append((command, output))
            
            # Rerun to update display
            st.rerun()

with col2:
    st.subheader("Quick Commands")
    
    for safe_cmd in SAFE_COMMANDS[:8]:
        if st.button(f"📟 {safe_cmd}", key=f"btn_{safe_cmd}"):
            output = execute_command(safe_cmd)
            st.session_state.command_history.append((safe_cmd, output))
            st.rerun()
    
    st.divider()
    
    st.subheader("System Info")
    st.code(f"Directory: {st.session_state.current_dir}")
    
    # Show disk usage
    if st.button("Show Disk Usage"):
        output = execute_command("df -h")
        st.text(output)
    
    if st.button("Show Processes"):
        output = execute_command("ps aux --sort=-%cpu | head -10")
        st.text(output)

# File browser
with st.expander("📁 File Browser"):
    try:
        files = os.listdir(st.session_state.current_dir)
        cols = st.columns(4)
        for idx, file in enumerate(files[:12]):
            filepath = os.path.join(st.session_state.current_dir, file)
            is_dir = os.path.isdir(filepath)
            icon = "📁" if is_dir else "📄"
            
            with cols[idx % 4]:
                if st.button(f"{icon} {file[:15]}", key=f"file_{idx}"):
                    if is_dir:
                        os.chdir(filepath)
                        st.session_state.current_dir = os.getcwd()
                        st.rerun()
                    else:
                        try:
                            with open(filepath, 'r') as f:
                                content = f.read(500)
                                st.text_area(f"Content of {file}", content, height=150)
                        except:
                            st.write(f"Cannot read {file}")
    except:
        st.error("Cannot list directory")

st.markdown("---")
st.caption(f"Running on: {sys.platform} | Current user: {os.getlogin()} | CWD: {st.session_state.current_dir}")

# SECURITY NOTES
with st.expander("⚠️ Important Security Information"):
    st.markdown("""
    **This is running REAL Linux commands with these risks:**
    
    1. **Arbitrary code execution** - Users can run ANY command
    2. **File system access** - Can read/modify/delete files
    3. **Network access** - Can make network requests
    4. **Process control** - Can start/stop processes
    
    **Safety measures you MUST implement:**
    
    ```python
    # 1. Use Docker containerization
    # 2. Implement command whitelisting
    # 3. Run as unprivileged user
    # 4. Set resource limits
    # 5. Use timeouts
    # 6. Isolate filesystem
    # 7. Monitor commands
    ```
    
    **NEVER deploy this publicly without proper security!**
    """)
