from cs_orchestration.config.settings import Settings, load_settings


def test_settings_model_does_not_read_environment_variables(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ORDER_BUSINESS_API_BASE_URL", "https://oms.example.test")

    settings = Settings()

    assert settings.order_business_api.base_url is None


def test_load_settings_is_the_single_environment_reader(monkeypatch) -> None:
    monkeypatch.setenv("ORDER_BUSINESS_API_BASE_URL", "https://oms.example.test")
    monkeypatch.setenv("ORDER_BUSINESS_API_USER", "service-user")
    monkeypatch.setenv("ORDER_BUSINESS_API_PASSWORD", "service-password")
    monkeypatch.setenv("ORDER_BUSINESS_API_SECRET_KEY", "service-secret")
    monkeypatch.setenv("INTEGRATION_MODE", "real")

    settings = load_settings()

    assert settings.integration_mode == "real"
    assert settings.order_business_api.base_url == "https://oms.example.test"
    assert settings.order_business_api.credentials.username == "service-user"
    assert settings.order_business_api.credentials.password == "service-password"
    assert settings.order_business_api.credentials.secret_key == "service-secret"
