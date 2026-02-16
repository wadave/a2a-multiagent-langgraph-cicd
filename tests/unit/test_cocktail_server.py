from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mcp_servers.cocktail_mcp_server import cocktail_server as _mod

# Pure functions (not wrapped by @mcp.tool())
format_cocktail_details = _mod.format_cocktail_details
format_cocktail_summary = _mod.format_cocktail_summary
format_ingredient = _mod.format_ingredient
make_cocktaildb_request = _mod.make_cocktaildb_request

# @mcp.tool() wraps functions in FunctionTool; access the original via .fn
search_cocktail_by_name = _mod.search_cocktail_by_name.fn
list_cocktails_by_first_letter = _mod.list_cocktails_by_first_letter.fn
search_ingredient_by_name = _mod.search_ingredient_by_name.fn
list_random_cocktails = _mod.list_random_cocktails.fn
lookup_cocktail_details_by_id = _mod.lookup_cocktail_details_by_id.fn


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

SAMPLE_DRINK = {
    "idDrink": "11007",
    "strDrink": "Margarita",
    "strCategory": "Ordinary Drink",
    "strGlass": "Cocktail glass",
    "strAlcoholic": "Alcoholic",
    "strInstructions": "Rub the rim of the glass with the lime slice to make the salt stick to it.",
    "strDrinkThumb": "https://example.com/margarita.jpg",
    "strDrinkAlternate": None,
    "strTags": "IBA,Classic",
    "strIBA": "Contemporary Classics",
    "strIngredient1": "Tequila",
    "strIngredient2": "Triple sec",
    "strIngredient3": "Lime juice",
    "strIngredient4": None,
    "strMeasure1": "1 1/2 oz",
    "strMeasure2": "1/2 oz",
    "strMeasure3": "1 oz",
    "strMeasure4": None,
    "dateModified": "2015-08-18 14:42:59",
}

SAMPLE_INGREDIENT = {
    "idIngredient": "1",
    "strIngredient": "Vodka",
    "strType": "Vodka",
    "strAlcohol": "Yes",
    "strABV": "40",
    "strDescription": "Vodka is a distilled beverage.",
}


# ---------------------------------------------------------------------------
# Pure function tests: format_cocktail_summary
# ---------------------------------------------------------------------------


class TestFormatCocktailSummary:
    def test_basic(self):
        result = format_cocktail_summary(SAMPLE_DRINK)
        assert "11007" in result
        assert "Margarita" in result
        assert "Ordinary Drink" in result
        assert "Cocktail glass" in result
        assert "Alcoholic" in result
        assert "https://example.com/margarita.jpg" in result

    def test_missing_keys(self):
        result = format_cocktail_summary({})
        assert "N/A" in result

    def test_long_instructions_truncated(self):
        drink = {**SAMPLE_DRINK, "strInstructions": "x" * 200}
        result = format_cocktail_summary(drink)
        # Instructions are truncated to 150 chars + "..."
        assert "..." in result
        assert ("x" * 151) not in result


# ---------------------------------------------------------------------------
# Pure function tests: format_cocktail_details
# ---------------------------------------------------------------------------


class TestFormatCocktailDetails:
    def test_with_ingredients(self):
        result = format_cocktail_details(SAMPLE_DRINK)
        assert "Margarita" in result
        assert "Ingredients:" in result
        assert "Tequila" in result
        assert "Triple sec" in result
        assert "Lime juice" in result
        assert "1 1/2 oz" in result

    def test_no_ingredients(self):
        drink = {"idDrink": "1", "strDrink": "Test"}
        result = format_cocktail_details(drink)
        assert "Ingredients:" not in result

    def test_ingredient_without_measure(self):
        drink = {
            "idDrink": "1",
            "strDrink": "Test",
            "strIngredient1": "Salt",
            "strMeasure1": None,
        }
        result = format_cocktail_details(drink)
        assert "Salt" in result
        assert "Ingredients:" in result


# ---------------------------------------------------------------------------
# Pure function tests: format_ingredient
# ---------------------------------------------------------------------------


class TestFormatIngredient:
    def test_basic(self):
        result = format_ingredient(SAMPLE_INGREDIENT)
        assert "Vodka" in result
        assert "40" in result
        assert "Yes" in result

    def test_long_description_truncated(self):
        ingredient = {**SAMPLE_INGREDIENT, "strDescription": "y" * 400}
        result = format_ingredient(ingredient)
        assert "..." in result
        assert ("y" * 301) not in result

    def test_missing_description_key(self):
        ingredient = {k: v for k, v in SAMPLE_INGREDIENT.items() if k != "strDescription"}
        result = format_ingredient(ingredient)
        assert "No description available." in result


# ---------------------------------------------------------------------------
# Async tests: make_cocktaildb_request
# ---------------------------------------------------------------------------


class TestMakeCocktaildbRequest:
    @pytest.fixture(autouse=True)
    def _patch_client(self):
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"drinks": [SAMPLE_DRINK]}
        self.mock_response.raise_for_status = MagicMock()

        self.mock_client = AsyncMock()
        self.mock_client.get.return_value = self.mock_response

        with patch(
            "mcp_servers.cocktail_mcp_server.cocktail_server.http_client",
            self.mock_client,
        ):
            yield

    async def test_success(self):
        result = await make_cocktaildb_request("search.php", params={"s": "margarita"})
        assert result == {"drinks": [SAMPLE_DRINK]}
        self.mock_client.get.assert_awaited_once_with(
            "search.php", params={"s": "margarita"}
        )

    async def test_null_string_response(self):
        self.mock_response.json.return_value = "null"
        result = await make_cocktaildb_request("search.php")
        assert result is None

    async def test_null_drinks_value(self):
        self.mock_response.json.return_value = {"drinks": None}
        result = await make_cocktaildb_request("search.php")
        assert result is None

    async def test_http_error(self):
        self.mock_client.get.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )
        result = await make_cocktaildb_request("search.php")
        assert result is None

    async def test_request_error(self):
        self.mock_client.get.side_effect = httpx.RequestError("timeout")
        result = await make_cocktaildb_request("search.php")
        assert result is None


# ---------------------------------------------------------------------------
# MCP tool tests: search_cocktail_by_name
# ---------------------------------------------------------------------------


class TestSearchCocktailByName:
    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_found(self, mock_request):
        mock_request.return_value = {"drinks": [SAMPLE_DRINK]}
        result = await search_cocktail_by_name("margarita")
        assert "Found cocktails:" in result
        assert "Margarita" in result

    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_not_found(self, mock_request):
        mock_request.return_value = None
        result = await search_cocktail_by_name("nonexistent")
        assert result == "No cocktails found with that name."


# ---------------------------------------------------------------------------
# MCP tool tests: list_cocktails_by_first_letter
# ---------------------------------------------------------------------------


class TestListCocktailsByFirstLetter:
    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_valid_letter(self, mock_request):
        mock_request.return_value = {"drinks": [SAMPLE_DRINK]}
        result = await list_cocktails_by_first_letter("m")
        assert "Cocktails starting with 'M':" in result
        assert "Margarita" in result

    async def test_invalid_multi_char(self):
        result = await list_cocktails_by_first_letter("AB")
        assert "Invalid input" in result

    async def test_invalid_number(self):
        result = await list_cocktails_by_first_letter("1")
        assert "Invalid input" in result

    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_no_results(self, mock_request):
        mock_request.return_value = None
        result = await list_cocktails_by_first_letter("z")
        assert "No cocktails found" in result


# ---------------------------------------------------------------------------
# MCP tool tests: search_ingredient_by_name
# ---------------------------------------------------------------------------


class TestSearchIngredientByName:
    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_found(self, mock_request):
        mock_request.return_value = {"ingredients": [SAMPLE_INGREDIENT]}
        result = await search_ingredient_by_name("vodka")
        assert "Vodka" in result

    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_not_found(self, mock_request):
        mock_request.return_value = None
        result = await search_ingredient_by_name("nonexistent")
        assert result == "No ingredient found with that name."


# ---------------------------------------------------------------------------
# MCP tool tests: list_random_cocktails
# ---------------------------------------------------------------------------


class TestListRandomCocktails:
    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_success(self, mock_request):
        mock_request.return_value = {"drinks": [SAMPLE_DRINK]}
        result = await list_random_cocktails()
        assert "Margarita" in result

    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_failure(self, mock_request):
        mock_request.return_value = None
        result = await list_random_cocktails()
        assert result == "Could not fetch a random cocktail."


# ---------------------------------------------------------------------------
# MCP tool tests: lookup_cocktail_details_by_id
# ---------------------------------------------------------------------------


class TestLookupCocktailDetailsById:
    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_valid_id(self, mock_request):
        mock_request.return_value = {"drinks": [SAMPLE_DRINK]}
        result = await lookup_cocktail_details_by_id("11007")
        assert "Margarita" in result

    async def test_invalid_non_numeric(self):
        result = await lookup_cocktail_details_by_id("abc")
        assert "Invalid input" in result
        assert "must be a number" in result

    @patch(
        "mcp_servers.cocktail_mcp_server.cocktail_server.make_cocktaildb_request",
        new_callable=AsyncMock,
    )
    async def test_not_found(self, mock_request):
        mock_request.return_value = None
        result = await lookup_cocktail_details_by_id("99999")
        assert "No cocktail found with ID 99999" in result
