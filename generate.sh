#!/bin/bash
WORKSPACE_PATH=$(dirname "$(readlink -f "$0")")

builder="-G Ninja"

if [ "$1" == "make" ]; then
    builder=""
fi

cmake ${builder} .. \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=1 \
    -DCMAKE_INSTALL_PREFIX=${WORKSPACE_PATH}/install \
    -DBUILD_PY_FFI=ON \
    -DBUILD_MULTI_GPU=ON \
    -DCMAKE_CUDA_FLAGS="-lineinfo" \
    -DUSE_NVTX=ON \
    # -DNCCL_INCLUDE_DIRS=/home/cbsu/CUDA/nccl_2.25.1-1+cuda12.4_x86_64/include \
    # -DNCCL_LIBRARIES=/home/cbsu/CUDA/nccl_2.25.1-1+cuda12.4_x86_64/lib/libnccl.so \


