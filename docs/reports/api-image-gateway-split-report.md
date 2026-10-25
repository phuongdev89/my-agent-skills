# Image Generate / API Image verification

Ngày: 2026-10-25 (Asia/Saigon). Thực hiện solo theo yêu cầu người dùng.

## Phạm vi và kết quả

PASS: 17 test mới + 4 test hồi quy; hai skill hợp lệ; git diff --check không báo lỗi.

Test chạy logic cấu hình, định tuyến, đóng gói HTTP, giải mã JSON/SSE và CLI thực; chỉ HTTP transport được mock. Không gọi API thật hoặc built-in imagegen. Chưa xác minh live gateway, chất lượng ảnh sinh, hoặc model backend thực tế.

Kiểm tra gồm thứ tự mặc định/đảo thứ tự/chọn một gateway, fallback quota/quyền/dịch vụ, cấu hình tách biệt, override CLI chỉ tầng đầu, bảo toàn prompt/size/quality/ảnh, sub2api edits multipart khi có ảnh và generations JSON khi không có, dừng lỗi đầu vào/từ chối an toàn/timeout/mất kết nối/lỗi tải ảnh, hết provider, legacy, dry-run không mạng, che credential và không sửa .env. Ảnh trong test là fixture PNG, không phải kết quả tạo ảnh API.

Test hồi quy Aidancing được sửa đường dẫn mốc HEAD sang skills/aidancing-image vì đường dẫn image-generate/scripts/aidancing đã không còn trong HEAD trước thay đổi này. Validator cần -X utf8 trên Windows để đọc tiếng Việt.

## Terminal output thực

### Run 1

```text
python -m unittest discover -s tests/api-image -v
test_cwd_env_read_only_environment_precedence_and_empty_key (test_api_image.EnvFileTests.test_cwd_env_read_only_environment_precedence_and_empty_key) ... ok
test_bad_selector_timeout_stops_before_network (test_api_image.GatewayTests.test_bad_selector_timeout_stops_before_network) ... ok
test_cli_override_only_first_tier (test_api_image.GatewayTests.test_cli_override_only_first_tier) ... ok
test_default_order_and_first_success (test_api_image.GatewayTests.test_default_order_and_first_success) ... ok
test_dry_run_never_calls_network_and_cli_success_writes_image (test_api_image.GatewayTests.test_dry_run_never_calls_network_and_cli_success_writes_image) ... ok
test_errors_and_metadata_redact_credentials (test_api_image.GatewayTests.test_errors_and_metadata_redact_credentials) ... ok
test_exhaustion_bounded (test_api_image.GatewayTests.test_exhaustion_bounded) ... ok
test_failure_classification_stops_or_falls_back (test_api_image.GatewayTests.test_failure_classification_stops_or_falls_back) ... ok
test_fallback_isolates_credentials_models_and_preserves_inputs (test_api_image.GatewayTests.test_fallback_isolates_credentials_models_and_preserves_inputs) ... ok
test_json_sse_nested_response_and_refusal (test_api_image.GatewayTests.test_json_sse_nested_response_and_refusal) ... ok
test_legacy_aliases_and_protocols (test_api_image.GatewayTests.test_legacy_aliases_and_protocols) ... ok
test_missing_config_skips_without_borrowing_legacy (test_api_image.GatewayTests.test_missing_config_skips_without_borrowing_legacy) ... ok
test_missing_reference_stops_before_network (test_api_image.GatewayTests.test_missing_reference_stops_before_network) ... ok
test_model_not_reported_is_not_invented (test_api_image.GatewayTests.test_model_not_reported_is_not_invented) ... ok
test_network_timeout_disconnect_and_download_do_not_resubmit (test_api_image.GatewayTests.test_network_timeout_disconnect_and_download_do_not_resubmit) ... ok
test_selector_order_single_and_defaults (test_api_image.GatewayTests.test_selector_order_single_and_defaults) ... ok
test_sub2api_detects_reference_even_with_protocol_override (test_api_image.GatewayTests.test_sub2api_detects_reference_even_with_protocol_override) ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.642s

OK
exit_code=0
```

### Run 2

```text
python -m unittest discover -s tests/image-skill-split -v
test_aidancing_scripts_preserved (test_openai_image.ImageSkillSplitTests.test_aidancing_scripts_preserved) ... ok
test_cli_dry_run_modes (test_openai_image.ImageSkillSplitTests.test_cli_dry_run_modes) ... ok
test_gateway_payloads_preserve_reference (test_openai_image.ImageSkillSplitTests.test_gateway_payloads_preserve_reference) ... ok
test_removed_cli_flag_rejected (test_openai_image.ImageSkillSplitTests.test_removed_cli_flag_rejected) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.654s

OK
exit_code=0
```

### Run 3

```text
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/image-generate
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/api-image
git diff --check
Skill is valid!
Skill is valid!
exit_code=0
```
