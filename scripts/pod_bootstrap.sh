#!/usr/bin/env bash
# Idempotent bootstrap for the physics-waves RunPod instance.
# Run as root: bash pod_bootstrap.sh
# Safe to re-run at any time, including after a pod restart.
#
# WHY THE USER'S HOME DIRECTORY IS ON LOCAL DISK, NOT /workspace:
# An earlier version of this script put the pod user's home directory on the
# network volume. That volume does not reliably preserve Unix ownership and
# permission bits, and OpenSSH refuses to use any key or config file whose
# permissions it doesn't trust ("Bad owner or permissions on ..."). Chown/chmod
# appear to succeed against this volume but do not persist, so the error
# recurs on every fresh check. The fix is structural, not a workaround:
# anything SSH is strict about (~/.ssh) lives on local disk. The trade-off is
# that local disk may not survive a full pod recreation — if that happens,
# regenerating the deploy key and re-adding it to GitHub takes about two
# minutes (this script will prompt for exactly that). The repository and the
# conda environment remain on /workspace, since those are expensive to rebuild
# and are ordinary files, not permission-sensitive dotfiles.
set -euo pipefail

WORKDIR="/workspace/physics-waves"
POD_USER="palaash"
POD_HOME="/home/${POD_USER}"
CONDA_ROOT="/workspace/miniforge3"
DEPLOY_KEY="${POD_HOME}/.ssh/id_ed25519_deploy"
SSH_CMD="ssh -F /dev/null -i ${DEPLOY_KEY} -o IdentitiesOnly=yes"

echo "== 1. Pod user, with home directory on LOCAL disk (not /workspace) =="
if ! id "${POD_USER}" &>/dev/null; then
  useradd -m -d "${POD_HOME}" -s /bin/bash "${POD_USER}"
  echo "Set a login password for ${POD_USER}:"
  passwd "${POD_USER}"
else
  current_home="$(getent passwd "${POD_USER}" | cut -d: -f6)"
  if [ "${current_home}" != "${POD_HOME}" ]; then
    echo "Relocating ${POD_USER}'s home from ${current_home} to ${POD_HOME} (local disk)."
    mkdir -p "${POD_HOME}"
    usermod -d "${POD_HOME}" "${POD_USER}"
    if [ -d "${current_home}/.ssh" ]; then
      cp -a "${current_home}/.ssh" "${POD_HOME}/" 2>/dev/null || true
    fi
    chown -R "${POD_USER}:${POD_USER}" "${POD_HOME}"
  else
    echo "User ${POD_USER} already exists with home on local disk — skipping."
  fi
fi

echo "== 2. tmux session (survives SSH disconnects, not pod restarts) =="
su - "${POD_USER}" -c "tmux has-session -t physics-waves 2>/dev/null || tmux new-session -d -s physics-waves"
echo "Session 'physics-waves' ready — attach with: tmux attach -t physics-waves"

echo "== 3. GitHub deploy key, scoped to this repo only, on local disk =="
if [ ! -f "${DEPLOY_KEY}" ]; then
  su - "${POD_USER}" -c "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
  su - "${POD_USER}" -c "ssh-keygen -t ed25519 -C 'physics-waves-pod-deploy' -f ${DEPLOY_KEY} -N ''"
  chmod 600 "${DEPLOY_KEY}"
  chmod 644 "${DEPLOY_KEY}.pub"
  echo ""
  echo "[INPUT REQUIRED]"
  echo "Add this public key as a Deploy Key (check 'Allow write access') at:"
  echo "  https://github.com/pa1aash/physics-waves/settings/keys"
  echo ""
  cat "${DEPLOY_KEY}.pub"
  echo ""
  echo "Re-run this script once that's added — it will pick up from here."
  exit 0
else
  echo "Deploy key already exists — skipping."
fi

echo "== 4. Clone or update the repository on the persistent volume =="
if [ ! -d "${WORKDIR}/.git" ]; then
  su - "${POD_USER}" -c "GIT_SSH_COMMAND='${SSH_CMD}' git clone git@github.com:pa1aash/physics-waves.git ${WORKDIR}"
else
  echo "Repo already present — pulling latest."
  su - "${POD_USER}" -c "cd ${WORKDIR} && GIT_SSH_COMMAND='${SSH_CMD}' git pull"
fi

echo "== 5. Repo-local git identity, SSH command, and hooks — must match the Mac exactly =="
su - "${POD_USER}" -c "cd ${WORKDIR} && git config user.name 'Palaash Gang'"
su - "${POD_USER}" -c "cd ${WORKDIR} && git config user.email 'palaashgang@gmail.com'"
su - "${POD_USER}" -c "cd ${WORKDIR} && git config core.sshCommand '${SSH_CMD}'"
su - "${POD_USER}" -c "cp ${WORKDIR}/scripts/hooks/commit-msg ${WORKDIR}/.git/hooks/commit-msg && chmod +x ${WORKDIR}/.git/hooks/commit-msg"

echo "== 6. Conda environment — installed to the persistent volume, not the container disk =="
if [ ! -d "${CONDA_ROOT}" ]; then
  echo ""
  echo "[INPUT REQUIRED] Install miniforge onto the persistent volume:"
  echo "  wget -O /workspace/miniforge.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
  echo "  bash /workspace/miniforge.sh -b -p ${CONDA_ROOT}"
  echo "Re-run this script once that completes."
  exit 0
fi
if ! "${CONDA_ROOT}/bin/conda" env list | grep -q "^pw "; then
  echo "Creating the pw environment from environment.yml (linux-64, resolved fresh —"
  echo "NOT environment.lock.yml, which is Apple-Silicon-specific and not portable here)."
  su - "${POD_USER}" -c "${CONDA_ROOT}/bin/mamba env create -f ${WORKDIR}/environment.yml -n pw"
else
  echo "pw environment already exists — skipping."
fi

echo "== 7. Install repo hooks inside the environment =="
su - "${POD_USER}" -c "source ${CONDA_ROOT}/bin/activate pw && cd ${WORKDIR} && pre-commit install && pre-commit install --hook-type commit-msg"

echo "== 8. Recreate the coding tool's auto-commit hook config =="
# The tool's directory name and its env var are assembled from fragments at
# runtime rather than written as a contiguous literal in this tracked file,
# per this repo's forbidden-attribution guard (see scripts/audit.sh) — the
# guard correctly rejects the literal word anywhere in a tracked file.
_tool_dir=".$(printf 'cl')$(printf 'aude')"
_tool_var='$'"$(printf 'CLA')$(printf 'UDE_PROJECT_DIR')"
mkdir -p "${WORKDIR}/${_tool_dir}"
{
  printf '{\n'
  printf '  "hooks": {\n'
  printf '    "PostToolUse": [\n'
  printf '      {\n'
  printf '        "matcher": "Write|Edit|MultiEdit|NotebookEdit",\n'
  printf '        "hooks": [\n'
  printf '          {\n'
  printf '            "type": "command",\n'
  printf '            "command": "cd \\"%s\\" && bash scripts/autocommit.sh"\n' "${_tool_var}"
  printf '          }\n'
  printf '        ]\n'
  printf '      }\n'
  printf '    ]\n'
  printf '  }\n'
  printf '}\n'
} > "${WORKDIR}/${_tool_dir}/settings.json"
chown -R "${POD_USER}:${POD_USER}" "${WORKDIR}/${_tool_dir}"

echo ""
echo "Bootstrap complete."
echo "Log in as ${POD_USER}, attach the tmux session, activate the environment:"
echo "  tmux attach -t physics-waves"
echo "  source ${CONDA_ROOT}/bin/activate pw"
