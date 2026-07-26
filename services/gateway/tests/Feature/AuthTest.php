<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AuthTest extends TestCase
{
    use RefreshDatabase; // Очищает базу перед каждым тестом и накатывает миграции

    public function test_user_can_get_token_with_valid_credentials(): void
    {
        // Подготовка данных: создаем тестового юзера
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => bcrypt('secret123'),
        ]);

        // Выполнение: отправляем запрос на эндпоинт авторизации
        $response = $this->postJson('/api/auth/token', [
            'email' => 'test@example.com',
            'password' => 'secret123',
        ]);

        // Проверки
        $response->assertStatus(200);
        $response->assertJsonStructure([
            'access_token',
            'token_type',
        ]);
    }

    public function test_user_cannot_get_token_with_invalid_credentials(): void
    {
        User::factory()->create([
            'email' => 'test@example.com',
            'password' => bcrypt('secret123'),
        ]);

        // Пытаемся залогиниться с неправильным паролем
        $response = $this->postJson('/api/auth/token', [
            'email' => 'test@example.com',
            'password' => 'wrongpassword',
        ]);

        // Ожидаем ошибку валидации (422 Unprocessable Entity)
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['email']);
    }
}