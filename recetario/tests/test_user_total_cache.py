from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache as django_cache

from recetario.user_totals_cache import AllUserTotalsCache


class TestAllUserTotalsCache:
    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        self.user_totals = {
            1: {"unidades": 5, "productos": 10, "recetas": 15},
            2: {"unidades": 3, "productos": 6, "recetas": 9},
        }
        self.cache = AllUserTotalsCache(timeout=1)
        yield
        django_cache.clear()  # Limpiar cache después de cada test

    def test_get_with_empty_cache(self) -> None:
        """Test que la caché se computa cuando está vacía"""
        with patch.object(
            self.cache, "_compute_all_totals", return_value=self.user_totals
        ) as mock_compute:
            result = self.cache.get(1)

            mock_compute.assert_called_once()
            assert result == self.user_totals[1]
            assert django_cache.get("all_user_totals") == self.user_totals

    def test_get_with_existing_cache(self) -> None:
        """Test que usa la caché existente sin recalcular"""
        # Primera llamada para llenar la caché
        with patch.object(
            self.cache, "_compute_all_totals", return_value=self.user_totals
        ):
            self.cache.get(1)

        # Segunda llamada debería usar la caché
        with patch.object(self.cache, "_compute_all_totals") as mock_compute:
            result = self.cache.get(2)

            mock_compute.assert_not_called()
            assert result == self.user_totals[2]

    def test_get_for_nonexistent_user(self) -> None:
        """Test para usuario que no existe"""
        with patch.object(
            self.cache, "_compute_all_totals", return_value=self.user_totals
        ):
            result = self.cache.get(999)  # ID que no existe

            assert result == {"unidades": 0, "productos": 0, "recetas": 0}

    def test_invalidate(self) -> None:
        """Test que la invalidación limpia la caché"""
        # Llenar la caché
        with patch.object(
            self.cache, "_compute_all_totals", return_value=self.user_totals
        ):
            self.cache.get(1)

        assert django_cache.get("all_user_totals") is not None

        # Invalidar y verificar
        self.cache.invalidate()
        assert django_cache.get("all_user_totals") is None

    @patch("recetario.user_totals_cache.User.objects.all")
    @patch("recetario.user_totals_cache.Unidad.objects.filter")
    @patch("recetario.user_totals_cache.Producto.objects.filter")
    @patch("recetario.user_totals_cache.Receta.objects.filter")
    def test_compute_all_totals(
        self,
        mock_receta: MagicMock,
        mock_producto: MagicMock,
        mock_unidad: MagicMock,
        mock_users: MagicMock,
    ) -> None:
        """Test que _compute_all_totals hace las queries correctas"""
        # Configurar mocks
        mock_user1 = MagicMock(id=1)
        mock_user2 = MagicMock(id=2)
        mock_users.return_value = [mock_user1, mock_user2]

        mock_unidad.return_value.count.side_effect = [5, 3]
        mock_producto.return_value.count.side_effect = [10, 6]
        mock_receta.return_value.count.side_effect = [15, 9]

        # Ejecutar
        result = self.cache._compute_all_totals()

        # Verificar
        assert result == {
            1: {"unidades": 5, "productos": 10, "recetas": 15},
            2: {"unidades": 3, "productos": 6, "recetas": 9},
        }

        # Verificar llamadas a los mocks
        mock_users.assert_called_once()
        assert mock_unidad.call_count == 2
        assert mock_producto.call_count == 2
        assert mock_receta.call_count == 2
