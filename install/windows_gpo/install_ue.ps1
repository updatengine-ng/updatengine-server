    ###
    #   Script de déploiement d'UpdatEngine client
    ###

    # Chemin UNC vers le partage qui contient l'exécutable
    $SharedFolder = "\\dc.domain.lan\netlogon\Files"

    # Chemin vers le dossier temporaire local sur le poste pour éviter warning 'editeur inconnu' lorsqu'on installe via chemin UNC
    $LocalFolder = "C:\Windows\Temp"

    # Nom de l'exécutable
    $ExeName = "updatengine-client-setup.exe"

    # Argument(s) à associer à l'exécutable
    $ExeArgument = '/verysilent /server=https://updatengine.domain.lan:1979 /noproxy /delay=30 /cert="\\dc.domain.lan\netlogon\Files\cacert-ue.pem" /norestart /forceinstall'

    # Version cible de l'exécutable (obtenue sur une installation manuelle)
    $ExeVersion = "4.1.3.0"

    # Chemin vers l'exécutable une fois l'installation terminée
    $ExeInstallPath = "C:\Program Files (x86)\UpdatEngine client\updatengine-client.exe"

    # Le logiciel est-il déjà installé dans la bonne version ?
    $InstalledVersion = (Get-ItemProperty -Path $ExeInstallPath -ErrorAction SilentlyContinue).VersionInfo.FileVersion

    # L'URL de la tâche planifié est-il correct ?
    $URLCheck = schtasks /query /fo list /v /tn "updatengine"
    $URLOk = $URLCheck -notlike "*https://updatengine.domain.lan*"

    if(($InstalledVersion -eq $null) -or ($InstalledVersion -ne $null -and $InstalledVersion -ne $ExeVersion) -or (!$URLOk)){

       # Si $InstalledVersion n'est pas null et que la version est différente, il faut faire une mise à jour
       if($InstalledVersion -ne $null){
          Write-Output "Le logiciel va être mis à jour : $InstalledVersion -> $ExeVersion"
       }

       # Si le chemin réseau vers l'exécutable est valide, on continue
       if(Test-Path "$SharedFolder\$ExeName"){

         # Créer le dossier temporaire en local et copier l'exécutable sur le poste
         New-Item -ItemType Directory -Path "$LocalFolder" -ErrorAction SilentlyContinue
         Copy-Item "$SharedFolder\$ExeName" "$LocalFolder" -Force

         # Si l'on trouve bien l'exécutable en local, on lance l'installation
         if(Test-Path "$LocalFolder\$ExeName"){
            Start-Process -Wait -FilePath "$LocalFolder\$ExeName" -ArgumentList "$ExeArgument"
         }

         # On supprime l'exécutable à la fin de l'installation
         Remove-Item "$LocalFolder\$ExeName"

       }else{
         Write-Warning "L'exécutable ($ExeName) est introuvable sur le partage !"
       }
    }else{
       Write-Output "Le logiciel est déjà installé dans la bonne version !"
    }
