from typing import Dict, Generator
from unittest.mock import MagicMock, call, patch

import pytest
from django.core.cache import cache as django_cache

from recetario.user_totals_cache import UserTotals, UserTotalsCache


class TestUserTotalsCache:
    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        self.sample_data: Dict[int, UserTotals] = {
            1: {"unidades": 5, "productos": 10, "recetas": 15},
            2: {"unidades": 3, "productos": 6, "recetas": 9},
        }
        self.cache = UserTotalsCache(timeout=1)
        yield
        django_cache.clear()  # Limpiar cache después de cada test

    def test_get_with_empty_cache(self) -> None:
        """Test que computa los datos cuando no hay caché"""
        with patch.object(
            self.cache, "_compute_user_totals", return_value=self.sample_data[1]
        ) as mock_compute:
            result = self.cache.get(1)

            mock_compute.assert_called_once_with(1)
            assert result == self.sample_data[1]
            assert django_cache.get("user_totals_1") == self.sample_data[1]
            assert django_cache.get("all_users_with_totals") == {1}

    def test_get_with_existing_cache(self) -> None:
        """Test que usa la caché existente sin recalcular"""
        # Primera llamada para llenar la caché
        with patch.object(
            self.cache, "_compute_user_totals", return_value=self.sample_data[1]
        ):
            self.cache.get(1)

        # Segunda llamada debería usar la caché
        with patch.object(self.cache, "_compute_user_totals") as mock_compute:
            result = self.cache.get(1)

            mock_compute.assert_not_called()
            assert result == self.sample_data[1]

    def test_get_for_nonexistent_user(self) -> None:
        """Test para usuario que no existe"""
        with patch.object(
            self.cache,
            "_compute_user_totals",
            return_value={"unidades": 0, "productos": 0, "recetas": 0},
        ):
            result = self.cache.get(999)  # ID que no existe

            assert result == {"unidades": 0, "productos": 0, "recetas": 0}

    def test_invalidate_single_user(self) -> None:
        """Test que la invalidación limpia solo un usuario"""
        # Llenar la caché para dos usuarios
        with patch.object(
            self.cache,
            "_compute_user_totals",
            side_effect=[self.sample_data[1], self.sample_data[2]],
        ):
            self.cache.get(1)
            self.cache.get(2)

        # Invalidar solo el usuario 1
        self.cache.invalidate(1)

        assert django_cache.get("user_totals_1") is None
        assert django_cache.get("user_totals_2") == self.sample_data[2]
        assert django_cache.get("all_users_with_totals") == {2}

    def test_invalidate_all_users(self) -> None:
        """Test que la invalidación limpia toda la caché"""
        # Llenar la caché
        with patch.object(
            self.cache,
            "_compute_user_totals",
            side_effect=[self.sample_data[1], self.sample_data[2]],
        ):
            self.cache.get(1)
            self.cache.get(2)

        # Invalidar todo
        self.cache.invalidate()

        assert django_cache.get("user_totals_1") is None
        assert django_cache.get("user_totals_2") is None
        assert django_cache.get("all_users_with_totals") is None

    @patch("recetario.user_totals_cache.User.objects.get")
    @patch("recetario.user_totals_cache.Unidad.objects.filter")
    @patch("recetario.user_totals_cache.Producto.objects.filter")
    @patch("recetario.user_totals_cache.Receta.objects.filter")
    def test_compute_user_totals(
        self,
        mock_receta: MagicMock,
        mock_producto: MagicMock,
        mock_unidad: MagicMock,
        mock_user_get: MagicMock,
    ) -> None:
        """Test que _compute_user_totals hace las queries correctas"""
        # Configurar mocks
        mock_user = MagicMock(id=1)
        mock_user_get.return_value = mock_user

        mock_unidad.return_value.count.return_value = 5
        mock_producto.return_value.count.return_value = 10
        mock_receta.return_value.count.return_value = 15

        # Ejecutar
        result = self.cache._compute_user_totals(1)

        # Verificar
        assert result == {"unidades": 5, "productos": 10, "recetas": 15}

        # Verificar llamadas
        mock_user_get.assert_called_once_with(pk=1)
        mock_unidad.assert_called_once_with(user=mock_user)
        mock_producto.assert_called_once_with(user=mock_user)
        mock_receta.assert_called_once_with(user=mock_user)

    def test_update_users_list(self) -> None:
        """Test que _update_users_list mantiene correctamente la lista"""
        # Usuario 1
        self.cache._update_users_list(1)
        assert django_cache.get("all_users_with_totals") == {1}

        # Usuario 2
        self.cache._update_users_list(2)
        assert django_cache.get("all_users_with_totals") == {1, 2}

        # Usuario 1 otra vez (no duplicados)
        self.cache._update_users_list(1)
        assert django_cache.get("all_users_with_totals") == {1, 2}

    def test_remove_from_users_list(self) -> None:
        """Test que _remove_from_users_list elimina correctamente"""
        # Llenar lista
        django_cache.set("all_users_with_totals", {1, 2, 3}, timeout=3600)

        # Eliminar usuario 2
        self.cache._remove_from_users_list(2)
        assert django_cache.get("all_users_with_totals") == {1, 3}

        # Eliminar usuario que no existe
        self.cache._remove_from_users_list(99)
        assert django_cache.get("all_users_with_totals") == {1, 3}

    @patch.object(UserTotalsCache, "get")
    def test_warm_up_cache(self, mock_get: MagicMock) -> None:
        """Test que warm_up_cache precarga correctamente"""
        user_ids = [1, 2, 3]

        # Test con lista específica
        self.cache.warm_up_cache(user_ids)
        mock_get.assert_has_calls([call(1), call(2), call(3)], any_order=True)

        # Reset mock
        mock_get.reset_mock()

        # Test sin parámetros (debería usar todos los usuarios)
        with patch("recetario.user_totals_cache.User.objects") as mock_objects:
            mock_objects.values_list.return_value = [
                4,
                5,
                6,
            ]  # Configurar valores esperados
            self.cache.warm_up_cache()
            mock_get.assert_has_calls([call(4), call(5), call(6)], any_order=True)
