import os
import onnx
import onnx.version_converter
from onnxsim import simplify
from onnxruntime.quantization import QuantType, quantize_dynamic


# Path Setting
original_folder_path = r"C:\Users\Downloads\Model_ONNX"                          # The original folder.
quanted_folder_path = r"C:\Users\Downloads\Model_ONNX_Quanted"                   # The quanted folder.
model_path = os.path.join(original_folder_path, "Model.onnx")                    # The original fp32 model path.
quanted_model_path = os.path.join(quanted_folder_path, "Model_quanted.onnx")     # The quanted model stored path.


# Upgrade the Opset version. (optional process)
# model = onnx.load(model_path)
# model = onnx.version_converter.convert_version(model, 21)
# onnx.save(model, quanted_model_path)
# del model

# Preprocess, it also cost alot of memory during preprocess, you can close this command and keep quanting. Call subprocess may get permission failed on Windows system.
subprocess.run([f'python -m onnxruntime.quantization.preprocess --auto_merge --all_tensors_to_one_file --input {model_path} --output {quant_model_path}'], shell=True)

# Start Quantize
quantize_dynamic(
    model_input=quanted_model_path,
    model_output=quanted_model_path,
    per_channel=True,                                        # True for model accuracy but cost a lot of time during quanting process.
    reduce_range=False,                                      # True for some x86_64 platform.
    weight_type=QuantType.QInt8,                             # Int8 is official recommended. No obvious difference between Int8 and UInt8 format.
    extra_options={'ActivationSymmetric': True,              # True for inference speed. False may keep more accuracy.
                   'WeightSymmetric': True,                  # True for inference speed. False may keep more accuracy.
                   'EnableSubgraph': True,                   # True for more quant.
                   'ForceQuantizeNoInputCheck': False,       # True for more quant.
                   'MatMulConstBOnly': False                 # False for more quant. Sometime, the inference speed may get worse.
                   },
    nodes_to_exclude=None,                                   # Specify the node names to exclude quant process. Example: nodes_to_exclude={'/Gather'}
    use_external_data_format=False                           # Save the model into two parts.
)

# ONNX Model Optimizer
model, _ = simplify(
    model=onnx.load(quanted_model_path),
    include_subgraph=True,
    dynamic_input_shape=False,          # True for dynamic input.
    tensor_size_threshold="1.99GB",        # Must less than 2GB.
    perform_optimization=True,          # True for more optimize.
    skip_fuse_bn=False,                 # False for more optimize.
    skip_constant_folding=False,        # False for more optimize.
    skip_shape_inference=False,         # False for more optimize.
    mutable_initializer=False           # False for static initializer.
)
onnx.save(model, quanted_model_path)

# Convert the simplified model to ORT format.
optimization_style = "Runtime"          # ['Runtime', 'Fixed']; Runtime for XNNPACK/NNAPI/QNN/CoreML..., Fixed for CPU provider
target_platform = "arm"                 # ['arm', 'amd64']; The 'amd64' means x86_64 desktop, not means the AMD chip.
# Call subprocess may get permission failed on Windows system.
subprocess.run([f'python -m onnxruntime.tools.convert_onnx_models_to_ort --output_dir {quanted_folder_path} --optimization_style {optimization_style} --target_platform {target_platform} --enable_type_reduction {quanted_folder_path}'], shell=True)
