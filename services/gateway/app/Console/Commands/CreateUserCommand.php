<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Attributes\Description;
use Illuminate\Console\Attributes\Signature;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

#[Signature('user:create {email}')]
#[Description('Create a new user for the API Gateway')]
class CreateUserCommand extends Command
{
    /**
     * Execute the console command.
     */
    public function handle()
    {
        $email = $this->argument('email');

        // Проверяем, нет ли уже такого юзера
        if (User::where('email', $email)->exists()) {
            $this->error("Ошибка: Пользователь с email {$email} уже существует!");
            return Command::FAILURE;
        }

        // Интерактивно спрашиваем имя (с дефолтным значением)
        $name = $this->ask('Введите имя пользователя', 'API User');

        // Генерируем случайный пароль, чтобы админу не пришлось его придумывать
        $password = Str::random(12);

        User::create([
            'name' => $name,
            'email' => $email,
            'password' => Hash::make($password),
        ]);

        $this->info("Пользователь успешно создан!");
        $this->line("Email: <comment>{$email}</comment>");
        $this->line("Password: <comment>{$password}</comment>");

        return Command::SUCCESS;
    }
}