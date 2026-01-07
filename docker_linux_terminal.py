import streamlit as st
import docker
import tempfile
import os
import json

st.set_page_config(page_title="Docker Linux Terminal", layout="wide")

st.title("🐳 Docker Linux Terminal")
st.info("Each command runs in an isolated Docker container")

# Initialize Docker client
try:
    client = docker.from_env()
    st.success("✅ Docker connected")
except:
    st.error("❌ Docker not available. Install Docker Desktop.")
    st.stop()

# Session state
if 'command_history' not in st.session_state:
    st.session_state.command_history = []

def run_in_container(command, image="ubuntu:latest"):
    """Run command in Docker container"""
    try:
        # Create temporary directory for mounts
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run command
            container = client.containers.run(
                image=image,
                command=f"/bin/bash -c '{command}'",
                detach=False,
                stdout=True,
                stderr=True,
                remove=True,
                mem_limit="100m",
                cpu_period=100000,
                cpu_quota=50000,
                network_disabled=True,
                read_only=True
            )
            
            return container.decode('utf-8') if container else ""
    
    except docker.errors.ContainerError as e:
        return f"Container error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Available Docker images
IMAGES = {
    "Ubuntu": "ubuntu:latest",
    "Alpine": "alpine:latest",
    "Debian": "debian:latest",
    "CentOS": "centos:latest"
}

# UI Layout
col1, col2 = st.columns([3, 1])

with col1:
    selected_image = st.selectbox("Select Linux Distribution", list(IMAGES.keys()))
    
    # Predefined commands
    st.subheader("Common Commands")
    tab1, tab2, tab3 = st.tabs(["System", "Files", "Network"])
    
    with tab1:
        cols = st.columns(3)
        with cols[0]:
            if st.button("System Info"):
                output = run_in_container("uname -a", IMAGES[selected_image])
                st.session_state.command_history.append(("uname -a", output))
        with cols[1]:
            if st.button("Disk Usage"):
                output = run_in_container("df -h", IMAGES[selected_image])
                st.session_state.command_history.append(("df -h", output))
        with cols[2]:
            if st.button("Memory Info"):
                output = run_in_container("free -h", IMAGES[selected_image])
                st.session_state.command_history.append(("free -h", output))
    
    with tab2:
        cols = st.columns(3)
        with cols[0]:
            if st.button("List Files"):
                output = run_in_container("ls -la", IMAGES[selected_image])
                st.session_state.command_history.append(("ls -la", output))
        with cols[1]:
            if st.button("Current Dir"):
                output = run_in_container("pwd", IMAGES[selected_image])
                st.session_state.command_history.append(("pwd", output))
        with cols[2]:
            if st.button("Create Test File"):
                output = run_in_container("echo 'Test' > test.txt && cat test.txt", IMAGES[selected_image])
                st.session_state.command_history.append(("Create file", output))
    
    # Custom command
    st.subheader("Custom Command")
    custom_cmd = st.text_input("Enter command:", "echo 'Hello Linux'")
    
    if st.button("Execute Custom Command", type="primary"):
        output = run_in_container(custom_cmd, IMAGES[selected_image])
        st.session_state.command_history.append((custom_cmd, output))
        st.rerun()

with col2:
    st.subheader("Command History")
    
    for cmd, output in st.session_state.command_history[-10:]:
        with st.expander(f"$ {cmd[:30]}..." if len(cmd) > 30 else f"$ {cmd}"):
            st.code(output if output else "No output", language="text")
    
    if st.button("Clear History"):
        st.session_state.command_history = []
        st.rerun()

# Show container stats
with st.expander("📊 Container Statistics"):
    try:
        containers = client.containers.list(all=True)
        st.write(f"Total containers: {len(containers)}")
        
        for container in containers[:5]:
            st.write(f"**{container.name}** - {container.status}")
    except:
        st.write("No container info available")

# Installation instructions
with st.expander("🔧 Setup Instructions"):
    st.markdown("""
    **1. Install Docker:**
    ```bash
    # Ubuntu/Debian
    sudo apt update
    sudo apt install docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    
    # Windows/Mac: Install Docker Desktop
    ```
    
    **2. Pull Linux images:**
    ```bash
    docker pull ubuntu:latest
    docker pull alpine:latest
    docker pull debian:latest
    ```
    
    **3. Install Python dependencies:**
    ```bash
    pip install streamlit docker
    ```
    
    **4. Run the app:**
    ```bash
    streamlit run docker_linux_terminal.py
    ```
    """)

st.markdown("---")
st.caption("Each command runs in a fresh container. Changes are not persisted between commands.")
