# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.PHONY: install test test-integration lint format local-up local-down \
        terraform-plan terraform-apply terraform-destroy

install:
	uv sync --all-extras

test:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v -m integration

lint:
	uv run ruff check src/ deployment/ tests/

format:
	uv run ruff format src/ deployment/ tests/

local-up:
	docker compose up --build

local-down:
	docker compose down

# Terraform infrastructure commands
terraform-plan:
	cd deployment/terraform && ./deploy.sh staging plan

terraform-apply:
	cd deployment/terraform && ./deploy.sh staging apply

terraform-destroy:
	cd deployment/terraform && ./deploy.sh staging destroy

terraform-plan-prod:
	cd deployment/terraform && ./deploy.sh prod plan

terraform-apply-prod:
	cd deployment/terraform && ./deploy.sh prod apply
