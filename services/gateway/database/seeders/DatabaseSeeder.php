<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    use WithoutModelEvents;

    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // Создаем тестового пользователя для локальной разработки.
        // Пароль по умолчанию берется из UserFactory и равен 'password'
        User::factory()->create([
            'name' => 'System Admin',
            'email' => 'admin@example.com',
        ]);
    }
}